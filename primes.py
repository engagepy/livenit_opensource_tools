def prime():
  a=1
  b=1
  flag = None
  list = []

  while a != 1001:
    
    if a == 1:
      flag = False
      pass
    else:
      if a > 1:
        for i in range(2,1000):
          if (a % i) == 0:
            flag = True
            pass
    if flag:
      mes = f"{a} is not a Prime."
      list.append(mes)
      flag = None
      a += b
    else:
      mes = f"{a} is PRIME."
      list.append(mes)
      flag = None
      a += b
    print('Running Prime')
  return list
