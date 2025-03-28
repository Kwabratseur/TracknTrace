import markdown
import subprocess
from preprocessor import preProcessor


## Log = ""

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
