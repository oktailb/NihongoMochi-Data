#!/usr/bin/python3
import os
import glob
import time
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# Configuration
BASE_DIR = 'langs'
SOURCE_DIR = '../NihongoMochi/shared/src/commonMain/composeResources/files/grammar/lessons/'
SOURCE_LANG = 'en'
# Ajoutez ici les langues que vous souhaitez supporter (doit correspondre aux noms de dossiers)
TARGET_LANGS = {
#    'ar_SA/grammar': 'ar',
#    'bn_BD/grammar': 'bn',
#    'de_DE/grammar': 'de',
#    'es_ES/grammar': 'es',
    'fr_FR/grammar': 'fr',
    'in_ID/grammar': 'id',
    'it_IT/grammar': 'it',
#    'ja_JP/grammar': 'ja',
    'ko_KR/grammar': 'ko',
    'mn_MN/grammar': 'mn',
    'pt_BR/grammar': 'pt',
    'ru_RU/grammar': 'ru',
    'th_TH/grammar': 'th',
    'ua_UA/grammar': 'uk',
#    'vi_VN/grammar': 'vi',
#    'zh_CN/grammar': 'zh-CN'
}

def translate_html(html_content, target_lang):
    soup = BeautifulSoup(html_content, 'html.parser')
    translator = GoogleTranslator(source=SOURCE_LANG, target=target_lang)
    
    # On définit les balises contenant du texte à traduire
    tags_to_translate = ['h1', 'h2', 'h3', 'p', 'li', 'th', 'td', 'strong', 'em', 'b', 'i']
    
    for tag_name in tags_to_translate:
        for tag in soup.find_all(tag_name):
            # On parcourt les éléments contenus dans la balise
            # On ne traduit que les segments de texte directs (NavigableString)
            # Les balises imbriquées seront traitées séparément par la boucle principale
            for content in list(tag.contents): # list() pour éviter les problèmes de modification en cours d'itération
                # Dans BeautifulSoup, les segments de texte ont .name == None
                if content.name is None and content.strip():
                    try:
                        text_to_translate = str(content)
                        translated = translator.translate(text_to_translate)
                        if translated:
                            content.replace_with(translated)
                        time.sleep(0.05)
                    except Exception as e:
                        print(f"Erreur de traduction segment: {e}")

    return str(soup)

def main():
    # Liste des fichiers source (ceux à la racine de SOURCE_DIR)
    source_files = glob.glob(os.path.join(SOURCE_DIR, "*.html"))
    
    for lang_code, translator_code in TARGET_LANGS.items():
        target_dir = os.path.join(BASE_DIR, lang_code)
        
        # Créer le dossier s'il n'existe pas
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Création du dossier: {target_dir}")

        print(f"\n--- Traduction vers {lang_code.upper()} ---")
        
        for source_path in source_files:
            filename = os.path.basename(source_path)
            target_path = os.path.join(target_dir, filename)
            
            # On traduit si le fichier n'existe pas ou s'il est plus vieux que la source
            if not os.path.exists(target_path) or os.path.getmtime(source_path) > os.path.getmtime(target_path):
                print(f"Traduction de {filename}...")
                
                with open(source_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                translated_html = translate_html(content, translator_code)
                
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(translated_html)
                
                print(f"  -> Sauvegardé dans {target_dir}")
            else:
                print(f"Skipping {filename} (déjà à jour)")

if __name__ == "__main__":
    main()
