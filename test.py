from modules.recherche_web import recherche_web_bing, recherche_web_google, recherche_web_wikipedia

print("\n✅ Test Bing direct :")
print(recherche_web_bing("Qui est Steve Jobs ?"))

print("\n✅ Test Google direct :")
print(recherche_web_google("Qui est Steve Jobs ?"))

print("\n✅ Test Wikipedia direct :")
print(recherche_web_wikipedia("Steve Jobs"))