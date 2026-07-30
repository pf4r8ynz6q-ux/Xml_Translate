"""
A command-line tool to translate text content in Draw.Io-generated XML files.

This script parses an XML file, extracts text from 'mxCell' elements,
translates the text using the deep-translator library, and then saves the
translated content into a new XML file, preserving the original structure.
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

# Attempt to import deep_translator and handle missing library automatically
try:
    from deep_translator import GoogleTranslator
    from deep_translator.exceptions import TranslationNotFound
except ImportError:
    print("Error: 'deep_translator' library not found.")
    print("Attempting to install 'deep-translator' automatically via pip...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "deep-translator"])
        from deep_translator import GoogleTranslator
        from deep_translator.exceptions import TranslationNotFound
        print("Successfully installed 'deep-translator'!\n")
    except Exception as err:  # pylint: disable=broad-except
        print(f"Failed to install 'deep-translator' automatically: {err}", file=sys.stderr)
        print("Please run: pip install deep-translator", file=sys.stderr)
        sys.exit(1)

class TextExtractor(HTMLParser):
    """
    Extracts and reassembles text from HTML fragments inside XML values.

    This class parses HTML content to separate translatable text from
    HTML tags, allowing for translation while preserving the formatting.
    """
    def __init__(self):
        super().__init__()
        self.reset()
        self.parts = []
        self.texts_to_translate = []

    def handle_starttag(self, tag, attrs):
        """Stores the opening HTML tag as a string."""
        attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs)
        self.parts.append(f"<{tag}{' ' if attr_str else ''}{attr_str}>")

    def handle_endtag(self, tag):
        """Stores the closing HTML tag as a string."""
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        """Stores text content and adds it to the translation list if non-empty."""
        if data.strip():
            self.parts.append(data)
            self.texts_to_translate.append(data)
        else:
            self.parts.append(data)  # Preserve whitespace

    def handle_entityref(self, name):
        """Stores HTML entities like &nbsp;."""
        self.parts.append(f"&{name};")

    def get_reassembled_html(self, translated_texts):
        """
        Reconstructs the HTML content with translated text.

        Args:
            translated_texts (list): A list of translated text strings.

        Returns:
            str: The reassembled HTML string with translated content.
        """
        translated_iter = iter(translated_texts)
        reassembled_parts = []
        original_texts_set = set(self.texts_to_translate)

        for part in self.parts:
            if part in original_texts_set:
                try:
                    translated_val = next(translated_iter)
                    # If translation failed or returned None, fall back to the original text
                    if translated_val is None:
                        reassembled_parts.append(part)
                    else:
                        reassembled_parts.append(str(translated_val))
                except StopIteration:
                    # Fallback in case of mismatch
                    reassembled_parts.append(part)
            else:
                reassembled_parts.append(part)
        return "".join(reassembled_parts)

def translate_texts_batch(texts, dest_lang, src_lang='en'):
    """
    Translates a list of texts to the destination language using batch processing.

    Args:
        texts (list): A list of strings to translate.
        dest_lang (str): The target language code (e.g., 'es').
        src_lang (str): The source language code (e.g., 'en').

    Returns:
        list: A list of translated strings, or None if an error occurs.
    """
    if not texts:
        return []
    try:
        translator = GoogleTranslator(source=src_lang, target=dest_lang)
        return translator.translate_batch(texts)
    except TranslationNotFound as err:
        print(f"\nError: Could not find translation for a text segment: {err}",
              file=sys.stderr)
        return None
    except Exception as err:  # pylint: disable=broad-except
        print(f"\nAn error occurred during translation: {err}", file=sys.stderr)
        return None

def translate_xml_file(input_file, output_file, target_lang, source_lang):
    """
    Parses, translates, and saves the XML file.

    Args:
        input_file (str): Path to the input XML file.
        output_file (str): Path to save the translated XML file.
        target_lang (str): The target language code.
        source_lang (str): The source language code.
    """
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except ET.ParseError as err:
        print(f"Error: Failed to parse XML file '{input_file}'. {err}",
              file=sys.stderr)
        return

    # Find all 'mxCell' elements with a 'value' attribute to translate
    nodes = [
        elem for elem in root.findall(".//*[@value]")
        if elem.tag == 'mxCell' and elem.get('value', '').strip()
    ]

    if not nodes:
        print("No text nodes found to translate.")
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
        return

    total_nodes = len(nodes)
    print(f"Found {total_nodes} text nodes to translate.")

    for i, elem in enumerate(nodes, 1):
        parser = TextExtractor()
        parser.feed(elem.get('value'))

        if parser.texts_to_translate:
            # Batch translate all text segments from the current node
            translated = translate_texts_batch(
                parser.texts_to_translate, target_lang, source_lang
            )
            if translated is None:
                print("Stopping translation due to an error.", file=sys.stderr)
                return

            elem.set('value', parser.get_reassembled_html(translated))

        # Print progress to the console
        print(f"\rProgress: {i}/{total_nodes} nodes updated ({i / total_nodes:.0%})", end="")

    print("\nTranslation complete.")

    try:
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
        print(f"Translated file saved as: {output_file}")
    except OSError as err:
        print(f"\nError: Could not write to output file '{output_file}'. {err}",
              file=sys.stderr)

def main():
    """Parses command-line arguments and initiates the translation process."""
    parser = argparse.ArgumentParser(
        description='Translate text in Draw.Io-generated XML files.'
    )
    parser.add_argument(
        '--in', dest='input_file', required=True,
        help='Input XML file path.'
    )
    parser.add_argument(
        '--l', dest='target_lang', required=True,
        help='Target language code (e.g., "es", "fr", "de").'
    )
    parser.add_argument(
        '--in_l', dest='source_lang', default='en',
        help='Source language code (default: "en").'
    )
    parser.add_argument(
        '--out', dest='output_file', default=None,
        help='Output filename (default: [input]_[lang].xml).'
    )

    args = parser.parse_args()

    # Determine output filename if not explicitly provided
    output_file = args.output_file
    if not output_file:
        base, _ = os.path.splitext(args.input_file)
        output_file = f"{base}_{args.target_lang}.xml"

    translate_xml_file(
        args.input_file,
        output_file,
        args.target_lang,
        args.source_lang
    )

if __name__ == '__main__':
    main()
