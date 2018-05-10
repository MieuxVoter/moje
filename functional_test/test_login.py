from selenium import webdriver


from vote.models import User

browser = webdriver.Firefox()
browser.get('http://localhost:8000')

assert 'Jugement Majoritaire' in browser.title
