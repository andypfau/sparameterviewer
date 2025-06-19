import markdown
import os
import glob
import re


if __name__ == '__main__':
    
    INDIR = 'doc'
    OUTDIR = 'doc/html'

    for infile in glob.glob(f'{INDIR}/*.md'):
        outfile = os.path.join(OUTDIR, os.path.splitext(os.path.split(infile)[1])[0] + '.htm')

        with open(infile, 'r') as fp:
            md = fp.read()

        md = re.sub(r'\.md\)', '.htm)', md)
        md = re.sub(r'"\./([a-zA-Z0-9_+-]+).png"', '"../\\1.png"', md)
        
        os.makedirs(OUTDIR, exist_ok=True)
        
        htm = markdown.markdown(md)
        with open(outfile, 'w') as fp:
            fp.write(htm)
