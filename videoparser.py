from urllib.request import urlopen
from bs4 import BeautifulSoup
import re

def extract_mp4(url):

   try:
      page = urlopen(url)
   except:
      print("Error opening the URL")

   html = page.read()
   soup = BeautifulSoup(html, "html.parser")
   content = soup.findAll('source', {"type":"video/mp4"})

   for x in content:
      pattern = re.compile(r'(?<=src=").+?(?=")')
      x = pattern.findall(str(x))
      content = (x)      
   
   return content 
   
     

#  extract_mp4("https://imgur.com/wA6keKv")