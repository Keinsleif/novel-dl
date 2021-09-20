import sys

class NovelDLException(Exception):
    def console_message(self):
        print(self.return_message(),file=sys.stderr)
    def return_message(self):
        return "novel-dl: "+self.args[0]
    def return_id(self):
        return self.args[1]


def raise_error(msg,id=0):
    raise NovelDLException(msg,id)
