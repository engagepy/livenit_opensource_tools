#import pprint
def reverse(s):
  
  alpha = any(map(str.isalpha,s))
  digits = any(map(str.isdigit,s))
  lower = any(map(str.islower,s))
  upper = any(map(str.isupper,s))
  return alpha, digits, lower, upper



def NonAlphanumeric(s):
  list=[]
  char = []
  charcount = 0 
  print('Non-Alphanumeric characters are: ')
  for i in s:
    if(i.isalnum() == False):
      list.append(i)
      charcount += 1
  char.append(charcount)
  return char, list

