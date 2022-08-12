#import pprint
def prime():
  a=1
  flag = None
  list = []
  list_notprime = []
  count = 0
  while a != 11094:
 
    if a == 1:
      flag = False
      pass
    else:
      if a > 1:
        for i in range(2,a):
          if (a % i) == 0:
            flag = True
            pass
          pass
    if flag:
      mes = f"{a} not Prime."
      list_notprime.append(mes)
      flag = None
      a += 1
    else:
      mes = f'{a} is ♚ |'
      count += 1
      list.append(mes)
      flag = None
      a += 1
  mathops = len(list) + len(list_notprime)
  mes = f'{mathops} Math Operations || {count} Prime Numbers ♚'
  print(f'{mathops} tests done')
  print('Running Prime')
  list = ( " ".join(list))
  return list, mes, mathops, count
