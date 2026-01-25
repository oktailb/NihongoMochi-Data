#!/usr/bin/python3
import os
import glob
import time

# Configuration
BASE_DIR = 'langs'

def main():
    # Liste des fichiers source (ceux à la racine de SOURCE_DIR)
    langs = glob.glob(os.path.join(BASE_DIR, "*"))
    
    for lang in langs:
        lang = lang.replace('langs/', '')
        print(f"--- Packaging de '{lang}' ---")
        os.system(f"cd {BASE_DIR}/{lang}/grammar ; zip -q -9 ../grammar.zip *.html ; md5sum ../grammar.zip | cut -d ' ' -f 1 > ../grammar.md5")
        os.system(f"cd {BASE_DIR}/{lang}/ ; zip -q -9 ./data.zip *.json ; md5sum data.zip | cut -d ' ' -f 1 > data.md5")

    print(f"--- Packaging exercices ---")
    os.system(f"cd exercices ; zip -q -9 ../exercices.zip *.json ; md5sum ../exercices.zip | cut -d ' ' -f 1 > ../exercices.md5")
    print(f"--- Packaging grammar ---")
    os.system(f"cd common ; zip -q -9 ../grammar.zip grammar.json ; md5sum ../grammar.zip | cut -d ' ' -f 1 > ../grammar.md5")
    
if __name__ == "__main__":
    main()
