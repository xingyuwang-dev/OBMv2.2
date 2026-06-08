from numpy import floor


# 一个简单版本的进度条


#function meter(n,i)
#this function is handy for tracking the completion of a for or while loop
#INPUTS:
#n is the total size of the loop (i.e. the number of steps)
#i is the current index of the loop
#increment is the percentage increment to display (optional, default is 10)
#
#USE EXAMPLE
#for i=1:n
#  meter(n,i)
#  etc
#


def meter(n, i, increment=10):
    Now = floor(100 * i / n)
    if not hasattr(meter, "LAST") or Now < increment:
        meter.LAST = 0
    Next = meter.LAST + increment

    if Now >= Next:
        meter.LAST = Next
        print(f"{meter.LAST}% done")