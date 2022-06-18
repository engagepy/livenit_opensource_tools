#import pprint
def prime():
  a=1
  b=1
  flag = None
  list = []
  count = 0
  while a != 1001:
    
    if a == 1:
      flag = False
      pass
    else:
      if a > 1:
        for i in range(2,a):
          if (a % i) == 0:
            flag = True
            pass
    if flag:
      mes = f"{a} not Prime."
      list.append(mes)
      flag = None
      a += b
    else:
      mes = f'{a} == PRIME.'
      count += 1
      list.append(mes)
      flag = None
      a += b
  mes = f'{len(list)} Math Operations || {count} Prime found.'
  print(f'{len(list)} tests done')
  print('Running Prime')
  list = ( " ".join(list))
  return list, mes
