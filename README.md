# Draw.IO XML Translator

A command-line tool designed to seamlessly translate text content inside draw.io-generated XML files. 

This script parses an XML file, finds specific structural nodes (`mxCell`), safely extracts any text hidden within HTML tags, translates the text using Google Translate via the `deep-translator` library, and produces a new XML file with the translated content. Crucially, it preserves all original structural integrity and inline HTML formatting.

## Features

- **Smart Text Extraction**: Extracts only the translatable text, leaving HTML tags (like `<b>`, `<br>`, etc.) untouched.
- **Batch Translation**: Groups texts into batches to speed up the translation process.
- **Auto-Dependency Installation**: If you don't have the required `deep-translator` package installed, the script will attempt to install it via `pip` automatically.
- **Progress Tracking**: Provides real-time console feedback on translation progress.

## Prerequisites

- **Python 3.6+** must be installed on your system.
- An active internet connection (to reach the translation API and automatically install dependencies if needed).

## Usage

Run the script from your command line / terminal by invoking Python:

```bash
python xml_translate.py --in <input_file> --l <target_lang> [OPTIONS]
```

### Arguments

| Argument | Required | Description | Default |
| :--- | :---: | :--- | :--- |
| `--in` | **Yes** | The path to the source XML file you want to translate. | *None* |
| `--l` | **Yes** | The target language code (e.g., `es` for Spanish, `fr` for French, `de` for German). | *None* |
| `--in_l` | No | The source language code. | `en` (English) |
| `--out` | No | The path for the output XML file. | `<input_filename>_<target_lang>.xml` |

## Examples

**1. Basic Translation (English to Spanish)**
Translate `module1.xml` to Spanish. The output will automatically be saved as `module1_es.xml`.
```bash
python xml_translate.py --in module1.xml --l es
```

**2. Specifying a Custom Output File**
Translate `module1.xml` to French and save it directly to a specific folder/filename.
```bash
python xml_translate.py --in module1.xml --l fr --out translated/module1_french.xml
```

**3. Translating from a Non-English Source**
Translate a German (`de`) XML file into Japanese (`ja`).
```bash
python xml_translate.py --in course_de.xml --in_l de --l ja
```