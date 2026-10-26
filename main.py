import os
import sys

# Redirige la ejecución al archivo principal dentro de src/
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

if __name__ == "__main__":
    import main
    main.main()
