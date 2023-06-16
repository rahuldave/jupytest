import nbclient
import nbformat
import io
import importlib
import contextlib
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import traceback

class Context:
    def __init__(self, src):
        self.src = src

    def evaluate(self, s):
        # Evaluate expression in kernel's namespace
        result = eval(s, globals(), locals())
        return result

    def execute(self, s):
        # Execute code in kernel's namespace
        exec(s, globals(), locals())

    def __getattr__(self, name):
        return self.evaluate(name)

    def __getitem__(self, name):
        return self.evaluate(name)

# Paths
notebook_path = sys.argv[1]
test_module_path = sys.argv[2]

# Load the notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)
# Load the test module
spec = importlib.util.spec_from_file_location("test", test_module_path)
test_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_module)

testcounter = 0
testresults = []
for cell_index, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        # Execute the current cell

        #print(f"Executing cell {cell_index}...")
        #print(cell['source'])


        so = StringIO()
        se = StringIO()
        src = cell['source']
        lines = cell['source'].split('\n')
        lines2 = [line for line in lines if not line.startswith("%")]
        src = "\n".join(lines2)
        print(src)
        context = Context(src)
        with redirect_stdout(so), redirect_stderr(se):
            try:
                exec(src, globals(), locals())
            except Exception as e:
                print("Exception in user code:", e)

        context.stdout = so.getvalue()
        context.stderr = se.getvalue()

        # Check if the first line matches the format
        lines = cell['source'].split('\n')
        if lines and lines[0].startswith("### edTest("):
            # Extract test function name
            test_name = lines[0].split('(')[1].split(')')[0].strip()
            print(f"Found test function '{test_name}'")
            # Prepare the context object


            try:
                returnval = test_function(context)
                if returnval==None:
                    print(f"Test function '{test_name}' returned None. SUCCESS")
                else:
                    print(f"Test function '{test_name}' returned {returnval}. FAILURE")
            except:
                print(f"Test function '{test_name}' failed with exception:")
                print("".join(traceback.format_exception(*sys.exc_info())))
            # Run the test function
            test_function = getattr(test_module, test_name, None)
            if test_function:
                print(
                    f"Running test function '{test_name}'...with {context}"
                )
                try:
                    rval = test_function(context)
                except Exception as e:
                    print(f"Test function '{test_name}' failed with exception:", e)
                    rval = -1
                testcounter += 1
                testresults.append(rval==None)
            else:
                print(f"Test function '{test_name}' not found in test module.")

if all(testresults):
    print(f"Passed all {testcounter} tests")
    sys.exit(0)
else:
    print(f"Failed tests in {testresults}. Passed {sum(testresults)} out of {testcounter} tests")
    sys.exit(-1)
