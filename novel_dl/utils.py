import sys

class NovelDLException(Exception):
    def console_message(self):
        print("novel-dl: ",end="",file=sys.stderr)
        print(self.args[0],file=sys.stderr)
    def return_message(self):
        return "novel-dl: "+self.args[0]


def raise_error(msg):
    raise NovelDLException(msg)

