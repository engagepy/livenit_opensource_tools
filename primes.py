
def prime():
  a = 1
  flag = None
  list_prime = []
  list_notprime = []
  count = 0
  while a != 5059:
    flag = False if a == 1 else None
    
    if a > 1:
      flag = False  # Reset flag for each number > 1
      for i in range(2, a):
        if (a % i) == 0:
          flag = True
          break
          
    if flag:
      mes = f"{a} not Prime."
      list_notprime.append(mes)
    else:
      mes = f'{a} -'
      count += 1
      list_prime.append(mes)
    a += 1
    
  mathops = len(list_prime) + len(list_notprime)
  mes = f'{mathops} Math Operations || {count} Prime Numbers Detected'
  print(f'{mathops} tests done')
  print('Running Prime')
  list_prime = (" ".join(list_prime))
  return list_prime, mes, mathops, count
