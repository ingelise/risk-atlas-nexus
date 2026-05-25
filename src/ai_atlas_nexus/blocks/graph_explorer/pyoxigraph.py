from collections import defaultdict
from typing import Any, Dict, List, Optional, Set
from urllib.parse import quote, unquote

import inflect
import pyoxigraph
from pydantic import BaseModel

from ai_atlas_nexus.blocks.graph_explorer.base import ExplorerBase
from ai_atlas_nexus.blocks.graph_explorer.query_builder import (
    NEXUS_URI,
    SPARQLQueryBuilder,
)
from ai_atlas_nexus.data.knowledge_graph import *
from ai_atlas_nexus.exceptions import InvalidSPARQLQueryException


try:
    from txtai import Embeddings
except ImportError:
    Embeddings = None

ie = inflect.engine()


class PyoxigraphExplorer(ExplorerBase):

    def __init__(self, data):
        """
        Initialize Pyoxigraph Explorer by loading LinkML data into a pyoxigraph Store.

        Args:
            data: Container
                Container object, populated instance of the knowledge graph
        """
        self._data = data
        self._combined_cache = {}
        self._id_cache = {}
        self._collection_map = {}
        self._embeddings = None
        self._qb = SPARQLQueryBuilder()
        self._build_id_caches()
        self._store = self._load_data_to_store(data)

    def _build_id_caches(self):
        """
        A dict which is mapping ID to LinkML obj and a map for collection_key → ClassName for the
        SPARQL type filtering.
        """
        for class_name in self._data.model_fields_set:
            items = getattr(self._data, class_name) or []

            # build collection map: map collection key (e.g. "risks") to class name (e.g. "Risk")
            if items:
                item_types = set(type(item).__name__ for item in items)
                if len(item_types) == 1:
                    # Single type in collection: use it directly
                    self._collection_map[class_name] = item_types.pop()
                else:
                    # Mixed types: fallback to singularized class name

                    for item_type in item_types:
                        singular = ie.singular_noun(item_type)
                        self._collection_map[item_type] = (
                            singular.title()
                            if singular
                            else item_type.rstrip("s").title()
                        )

            # cache index
            for item in items:
                if hasattr(item, "id") and item.id:
                    self._id_cache[item.id] = item

    def get_all_classes(self):
        """
        Get all the class names that have data in the knowledge graph.

        Returns:
             list[str]
        """
        results = []
        rs = self._store.query(self._qb.get_all_classes())
        classes = [str(row["class"]) for row in rs]
        for uri_str in classes:
            if uri_str.startswith("<") and uri_str.endswith(">"):
                uri_str = uri_str[1:-1]
            if uri_str.startswith(NEXUS_URI):
                encoded_id = uri_str[len(NEXUS_URI) :]
                identifier = unquote(encoded_id)
                results.append(identifier)
        return results

    def _check_subclasses(self, result, class_name):
        # look for subclasses within container collections
        for collection_key, collection_data in self._data:
            instances = (
                collection_data if isinstance(collection_data, list) else []
            )

            for instance in instances:
                instance_type_name = type(instance).__name__
                possible_singular = ie.singular_noun(class_name)
                if instance_type_name.lower() == class_name.lower() or (
                    possible_singular
                    and instance_type_name.lower() == possible_singular.lower()
                ):
                    result.append(instance)

        return result

    def _load_data_to_store(self, data) -> pyoxigraph.Store:
        """
        Load Container into a pyoxigraph Store by building RDF quads from Pydantic objects.
        """
        store = pyoxigraph.Store()
        seen_iris = set()

        # Iterate all objects and add RDF quads
        for field_name in data.model_fields_set:
            items = getattr(data, field_name) or []
            if not isinstance(items, list):
                items = [items]

            for item in items:
                if not isinstance(item, BaseModel):
                    continue

                item_id = getattr(item, "id", None)
                if not item_id:
                    continue

                # URI-encode the ID for special characters
                encoded_id = quote(str(item_id), safe="")
                item_uri = pyoxigraph.NamedNode(f"{NEXUS_URI}{encoded_id}")

                # Skip duplicates
                if item_uri in seen_iris:
                    continue
                seen_iris.add(item_uri)

                # Add rdf:type quad
                class_name = type(item).__name__
                class_uri = pyoxigraph.NamedNode(f"{NEXUS_URI}{class_name}")
                rdf_type = pyoxigraph.NamedNode(
                    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
                )
                store.add(pyoxigraph.Quad(item_uri, rdf_type, class_uri, None))

                # Add property quads
                for field_name_attr, field_value in item:
                    if field_value is None or field_name_attr.startswith("_"):
                        continue

                    prop_uri = pyoxigraph.NamedNode(
                        f"{NEXUS_URI}{field_name_attr}"
                    )

                    if isinstance(field_value, str):
                        obj = pyoxigraph.Literal(field_value)
                    elif isinstance(field_value, bool):
                        obj = pyoxigraph.Literal(
                            str(field_value).lower(),
                            datatype=pyoxigraph.NamedNode(
                                "http://www.w3.org/2001/XMLSchema#boolean"
                            ),
                        )
                    elif isinstance(field_value, int):
                        obj = pyoxigraph.Literal(
                            str(field_value),
                            datatype=pyoxigraph.NamedNode(
                                "http://www.w3.org/2001/XMLSchema#integer"
                            ),
                        )
                    elif isinstance(field_value, float):
                        obj = pyoxigraph.Literal(
                            str(field_value),
                            datatype=pyoxigraph.NamedNode(
                                "http://www.w3.org/2001/XMLSchema#decimal"
                            ),
                        )
                    elif isinstance(field_value, list):
                        # Add multiple quads for list values
                        for list_item in field_value:
                            if isinstance(list_item, str):
                                obj = pyoxigraph.Literal(list_item)
                                store.add(
                                    pyoxigraph.Quad(
                                        item_uri, prop_uri, obj, None
                                    )
                                )
                        continue
                    else:
                        obj = pyoxigraph.Literal(str(field_value))

                    store.add(pyoxigraph.Quad(item_uri, prop_uri, obj, None))

        return store

    def _uri_to_pydantic(self, node: pyoxigraph.NamedNode) -> Optional[Any]:
        """
        Convert a pyoxigraph NamedNode to a Pydantic object via id_cache.
        """

        uri_str = str(node)
        # NamedNode.__str__() includes angle brackets, e.g. "<http://...>"
        if uri_str.startswith("<") and uri_str.endswith(">"):
            uri_str = uri_str[1:-1]
        if uri_str.startswith(NEXUS_URI):
            encoded_id = uri_str[len(NEXUS_URI) :]
            identifier = unquote(encoded_id)
            return self._id_cache.get(identifier)
        return None

    def _get_embeddings(self):
        """Lazy-initialize and return a txtai Embeddings instance."""
        if self._embeddings is None:
            if Embeddings is None:
                raise ImportError(
                    "txtai is required for semantic similarity. Install with: pip install txtai"
                )
            self._embeddings = Embeddings()
        return self._embeddings

    def get_all(
        self,
        class_name: Optional[str] = None,
        taxonomy: Optional[str] = None,
        vocabulary: Optional[str] = None,
        document: Optional[str] = None,
    ):
        """
        Get all instances of a specified class with optional filters.

        Args:
            class_name: str | None
                Name of the class to retrieve
            taxonomy: str | None
                (Optional) Filter by taxonomy id
            vocabulary: str | None
                (Optional) Filter by vocabulary id
            document: str | None
                (Optional) Filter by document id

        Returns:
            list: List of Pydantic instances
        """
        class_names = []

        if class_name is None:
            class_names = self.get_all_classes()
        elif isinstance(class_name, str):
            class_names.append(class_name)
        else:
            class_names = class_name

        cache_key = (
            (
                tuple(class_names)
                if isinstance(class_names, list)
                else class_name
            ),
            taxonomy,
            vocabulary,
            document,
        )

        if cache_key in self._combined_cache:
            return self._combined_cache[cache_key]

        result = []
        seen_ids = set()

        for key in class_names:
            # Resolve collection key from model
            if key not in self._data.model_fields_set:
                for k in self._data.model_fields_set:
                    if k.lower().replace("_", "") == key.lower().replace(
                        "_", ""
                    ):
                        key = k
                        break

            class_name_camel = self._collection_map.get(key)

            if not class_name_camel:
                # Try to find by class name (e.g., "Risk" or "Action") via _check_subclasses
                subclass_results = self._check_subclasses([], key)
                for item in subclass_results:
                    item_id = getattr(item, "id", None)
                    if item_id and item_id not in seen_ids:
                        result.append(item)
                        seen_ids.add(item_id)
                    elif not item_id:
                        result.append(item)
                continue

            query = self._qb.get_all_instances_of_class(
                class_name_camel, taxonomy, vocabulary, document
            )

            for solution in self._store.query(query):
                node = solution["s"]
                if node:
                    obj = self._uri_to_pydantic(node)
                    if obj:
                        item_id = getattr(obj, "id", None)
                        if item_id and item_id not in seen_ids:
                            result.append(obj)
                            seen_ids.add(item_id)
                        elif not item_id:
                            result.append(obj)

        self._combined_cache[cache_key] = result
        return result

    def get_by_id(self, class_name, identifier):
        """
        Get a single instance by its identifier.

        Args:
            class_name: str | None
                Name of the class (the collection key in data)
            identifier: str
                Value of the identifier field

        Returns:
            Optional[Dict[str, Any]]
                The matching instance or None
        """
        return self._id_cache.get(identifier)

    def get_by_attribute(self, class_name, attribute, value):
        """
        Get all the instances that match a specific attribute value.

        Args:
            class_name: str
                Name of the class (the collection key in data)
            attribute: str
                Attribute name to filter by
            value: Any
                Value to match

        Returns:
            List[Dict[str, Any]]
                List of matching instances
        """
        # Resolve class name to camel case
        class_name_camel = self._collection_map.get(class_name, class_name)

        # Format value as SPARQL literal
        if isinstance(value, str):
            sparql_value = f'"{value}"'
        else:
            sparql_value = f'"{value}"'

        query = self._qb.get_instances_by_attribute(
            class_name_camel, attribute, sparql_value
        )

        matches = []
        for solution in self._store.query(query):
            node = solution["s"]
            if node:
                obj = self._uri_to_pydantic(node)
                if obj:
                    matches.append(obj)

        return matches

    def get_attribute(self, class_name, identifier, attribute):
        """
        Get a specific attribute value from an instance.

        Args:
            class_name: str
                Name of the class
            identifier: str
                Identifier of the instance
            attribute: str
                Attribute name to retrieve

        Returns:
            Any
                The attribute value or None
        """
        instance = self.get_by_id(class_name, identifier)
        if instance and hasattr(instance, attribute):
            return getattr(instance, attribute)
        return None

    def query(self, class_name, **kwargs):
        """
        A query method using keyword arguments.

        Args:
            class_name: Union[str | list]
                Name of the class (the collection key in data)
            **kwargs:
                The attribute-value pairs to filter by

        Returns:
            list[Dict[str, Any]]
                List of matching instances
        """
        return self.filter_instances(class_name, kwargs)

    def filter_instances(self, class_name, filters):
        """
        Filter instances by multiple criteria.

        Args:
            class_name: Union[str | list]
                Name of the class (the collection key in data)
            filters: Dict[str, Any]
                Dictionary of attribute-value pairs

        Returns:
            List[Dict[str, Any]]
                List of matching instances
        """
        instances = self.get_all(class_name)
        matches = []

        for instance in instances:
            match = []
            for k, v in filters.items():
                if v is not None:
                    if (
                        type(getattr(instance, k)) == str
                        and getattr(instance, k) == v
                    ) or (
                        type(getattr(instance, k)) == list
                        and v in getattr(instance, k)
                    ):
                        match.append(1)
                    else:
                        match.append(0)

            if not 0 in match:
                matches.append(instance)

        return matches

    def filter_ids_by_type(self, ids, disallowed_types):
        """
        Filter a list of IDs to remove ones of type

        Args:
            ids: List[str]
                List of ids to filter
            allowed_types: List[str]
                The types to allow

        Returns:
            List[str]

        """
        return [
            id_
            for id_ in ids
            if id_ in self._id_cache
            and type(self._id_cache[id_]).__name__ not in disallowed_types
        ]

    def arrange_ids_by_type(self, ids):
        """
        Arrange a list of IDs to organise by type

        Args:
            ids: List[str]
                List of ids to filter

        Returns:
            dict

        """
        result = defaultdict(list)
        for id_ in ids:
            if id_ in self._id_cache:
                r_type = type(self._id_cache[id_]).__name__
                if result.get(r_type):
                    result[r_type].append(id_)
                else:
                    result[r_type] = [id_]

        return result

    def sparql_query(self, query_str: str) -> List[Dict[str, str]]:
        """
        Execute a raw SPARQL query against the store.

        Args:
            query_str: str
                SPARQL query string

        Returns:
            list[dict]: Query results as list of dicts
        """
        try:
            try:
                results = self._store.query(query_str)
            except SyntaxError as e:
                raise InvalidSPARQLQueryException(str(e))

            if isinstance(results, bool):
                return [{"result": str(results)}]

            output = []
            var_list = (
                list(results.variables)
                if hasattr(results, "variables")
                else []
            )

            for solution in results:
                row_dict = {}
                for var in var_list:
                    val = solution[var]
                    if val is not None:
                        if isinstance(val, pyoxigraph.NamedNode):
                            row_dict[str(var)] = str(val)
                        elif isinstance(val, pyoxigraph.Literal):
                            row_dict[str(var)] = val.value
                        else:
                            row_dict[str(var)] = str(val)
                    else:
                        row_dict[str(var)] = None
                output.append(row_dict)
            return output
        except InvalidSPARQLQueryException:
            raise
        except Exception as e:
            return [{"error": str(e)}]

    @staticmethod
    def _get_result_type(term) -> str:
        if isinstance(term, pyoxigraph.Literal):
            return "literal"
        elif isinstance(term, pyoxigraph.NamedNode):
            return "uri"
        elif isinstance(term, pyoxigraph.BlankNode):
            return "bnode"
        else:
            raise ValueError(f"Unknown type: {type(term)}")

    def clear_cache(self):
        """
        Manually clear combined cache. ID cache is intentionally not cleared
        since it's built from Pydantic data and should persist across queries.
        """
        self._combined_cache.clear()
