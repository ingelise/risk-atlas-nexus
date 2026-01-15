#!/usr/bin/env python3
"""Test script to debug import issues."""

import sys
import traceback


print("=" * 60)
print("Testing imports...")
print("=" * 60)

# Test 1: Basic imports
try:
    print("\n1. Testing basic imports...")
    import ai_atlas_nexus
    print("   ✓ ai_atlas_nexus")
except Exception as e:
    print(f"   ✗ ai_atlas_nexus: {e}")
    traceback.print_exc()

# Test 2: Metadata base
try:
    print("\n2. Testing metadata_base...")
    from ai_atlas_nexus.metadata_base import InferenceEngineType
    print("   ✓ InferenceEngineType")
    print(f"     HF_ZERO_GPU = {InferenceEngineType.HF_ZERO_GPU}")
except Exception as e:
    print(f"   ✗ metadata_base: {e}")
    traceback.print_exc()

# Test 3: Inference params
try:
    print("\n3. Testing inference params...")
    from ai_atlas_nexus.blocks.inference.params import (
        HFZeroGPUInferenceEngineParams,
        InferenceEngineCredentials,
    )
    print("   ✓ HFZeroGPUInferenceEngineParams")
    print("   ✓ InferenceEngineCredentials")
except Exception as e:
    print(f"   ✗ inference params: {e}")
    traceback.print_exc()

# Test 4: Base inference engine
try:
    print("\n4. Testing base inference engine...")
    from ai_atlas_nexus.blocks.inference.base import InferenceEngine
    print("   ✓ InferenceEngine")
except Exception as e:
    print(f"   ✗ base inference engine: {e}")
    traceback.print_exc()

# Test 5: HFZeroGPU engine
try:
    print("\n5. Testing HFZeroGPUInferenceEngine...")
    from ai_atlas_nexus.blocks.inference.hf_zero_gpu import HFZeroGPUInferenceEngine
    print("   ✓ HFZeroGPUInferenceEngine")
except Exception as e:
    print(f"   ✗ HFZeroGPUInferenceEngine: {e}")
    traceback.print_exc()

# Test 6: Import from __init__
try:
    print("\n6. Testing import from __init__...")
    from ai_atlas_nexus.blocks.inference import HFZeroGPUInferenceEngine
    print("   ✓ HFZeroGPUInferenceEngine (from __init__)")
except Exception as e:
    print(f"   ✗ HFZeroGPUInferenceEngine (from __init__): {e}")
    traceback.print_exc()

# Test 7: Import test module
try:
    print("\n7. Testing test module imports...")
    from tests.ai_atlas_nexus.blocks.inference.test_hf_zero_gpu import (
        TestHFZeroGPUInferenceEngine,
    )
    print("   ✓ TestHFZeroGPUInferenceEngine")
except Exception as e:
    print(f"   ✗ test module: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Import test complete")
print("=" * 60)
