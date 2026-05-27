# neil.douglas@york.ac.uk

import sys
import os
from easybuild.framework.easyconfig.easyconfig import ActiveMNS
from easybuild.framework.easyconfig.easyconfig import EasyConfig
from easybuild.tools.options import set_up_configuration

def validate(path):
    try:
        set_up_configuration()

        # Parse the EasyConfig file but don't validate it
        ec = EasyConfig(path, validate=False)

        # Use the module naming scheme to get the module name and then create the expected .eb filename
        mns = ActiveMNS()
        print(f"Module Naming Scheme: " + mns.det_full_module_name(ec))

        expected = mns.det_full_module_name(ec).replace('/', '-')+'.eb'
        actual = os.path.basename(path)

        if actual != expected:
            print(f"   Detected: {actual}")
            print(f"   Expected: {expected}")
            print(f"❌ Mismatch in {path}")
            return False

        print(f"   Detected: {actual}")
        print(f"   Expected: {expected}")
        print(f"✅ {actual} matches internal metadata.")
        return True

    except Exception as e:
        print(f"💩 Failed to parse {path}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_eb.py <path_to_eb_file>")
        sys.exit(1)

    files = sys.argv[1:]
    results = [validate(f) for f in files]
    sys.exit(0 if all(results) else 1)
