import skrf

class CitiWriter:
    @staticmethod
    def write(nw: skrf.Network, filename: str):
        with open(filename,'w') as fp:
            fp.write('CITIFILE A.01.01\n')
            for comment in nw.comments.splitlines():
                fp.write(f'# {comment}\n')
            fp.write('NAME DATA\n')
            fp.write(f'VAR FREQ MAG {len(nw.f)}\n')
            for ip in range(nw.nports):
                for ep in range(nw.nports):
                    fp.write(f'DATA S[{ep+1},{ip+1}] RI\n')
            fp.write('VAR_LIST_BEGIN\n')
            for f in nw.f:
                fp.write(f'{f}\n')
            fp.write('VAR_LIST_END\n')
            for ip in range(nw.nports):
                for ep in range(nw.nports):
                    fp.write('BEGIN\n')
                    for s in nw.s[:,ep,ip]:
                        s: complex
                        fp.write(f'{s.real},{s.imag}\n')
                    fp.write('END\n')
            fp.write(')\n')
