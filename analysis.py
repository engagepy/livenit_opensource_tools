#import pprint
def reverse(s):
  alphabet_count = 0
  digit_count = 0
  upper_count = 0
  lower_count = 0
  space_count = 0
  for i in s:
    if any(map(str.isalpha,i)):
      alphabet_count += 1
  for i in s:
    if any(map(str.isdigit,i)):
      digit_count += 1

  for i in s:
    if any(map(str.isupper,i)):
      upper_count += 1

  for i in s:
    if any(map(str.islower,i)):
      lower_count += 1
  
  for i in s:
    if i == ' ':
      space_count += 1
  
  total = alphabet_count + digit_count + space_count
  return alphabet_count, digit_count, upper_count, lower_count, space_count, total



def NonAlphanumeric(s, total):
  list=[]
  nogo = [' ']
  char = []
  charcount = 0 
  for i in s:
    if(i.isalnum() == False):
      if i not in nogo:
        charcount += 1
        if i not in list:
          list.append(i)
        
  char.append(charcount)
  sim = " "
  for i in list:
    sim += i +" "
  total += charcount
  return char, list, sim, total

