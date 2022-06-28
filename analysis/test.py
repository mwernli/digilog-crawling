class foo(object):
    def __init__(self, x):
        self.x = x
        # print ("hi")
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        # print ("bye")
        del self.x
counter = 0
while True:
    counter += 1
    with foo(counter) as a:
        print (a.x ) # This works, because a.x still exists
    # bye is printed at this point
    # print (a.x )# This fails, because we deleted the x attribute in __exit__ and the with is done
    # a still exists until it goes out of scope, but it's logically "dead" and empty
    if counter > 20:
        break