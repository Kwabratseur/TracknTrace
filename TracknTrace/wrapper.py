import markdown
import subprocess
import os
import sys
from TracknTrace.preprocessor import preProcessor


## Log = ""
def main():

    data, Log, instance = preProcessor.main()
    ## print(Log)
    with open('{}_result.md'.format(instance), 'w') as f:
        f.write(Log)
    html_string = markdown.markdown(Log, extensions=['tables'])
    ## print(html_string)
    with open('{}_result.html'.format(instance), 'w') as f:
        f.write(html_string)

    subprocess.Popen('{start} {path}'.format(  ## Open generated report in firefox
        start='firefox', path='{}_result.html'.format(instance)), shell=True)

if __name__ == "__main__":
    print(("%s is being run directly" % __name__))
    try:
        main()
    except RuntimeError:
        print("Error")
        os._exit(os.EX_OK)
else:
    print("---\n{}\n---\nV0.0.1 is being imported\n---".format(sys.argv[0]))
