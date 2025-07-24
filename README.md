[![Build Status](https://github.com/raskolnikoff/puml2class/actions/workflows/ci.yml/badge.svg)](https://github.com/raskolnikoff/puml2class/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

# puml2class

**puml2class** is a CLI tool for generating Swift class definitions from PlantUML class diagrams (.puml).  
Designed for model-driven development, it supports advanced type mapping, multiple classes per file, and documentation extraction.

## Features

- Converts PlantUML class diagrams (.puml) to Swift class files (.swift), one file per class
- Supports arrays, optionals, generics (List/Map/Set/Result) with automatic Swift idiom mapping
- Leaves custom types (e.g., `Map`, `Chunk`) unmapped in Swift output, so you can define them as needed in your Swift codebase
- Handles properties, methods (with multiple arguments, custom types), and return types robustly
- Extracts comments (`'` or `//` lines) as Swift `///` documentation comments
- CLI: input/output directory, batch processing
- Ready for multi-language backend (future: TypeScript, Kotlin, Java, ...)

## Custom Types

If your PlantUML uses custom types (such as `Map`, `Chunk`, etc.), the generated Swift code will reference these types directly. You must define these types in your Swift project for the code to compile successfully. This approach provides flexibility for future extensions and custom class support.

## Usage

```bash
python src/puml2class.py --in uml --out templates
```
- `uml/` : input directory for PlantUML .puml files
- `templates/` : output directory for generated Swift files

## Requirements

- Python 3.8+ (only standard library dependencies: `re`, `os`, `argparse`)

## .gitignore (recommended)

```
# Build & generated artifacts
__pycache__/
*.py[cod]
templates/*
uml/*
.env
.venv
.idea/
```

## Example

**PlantUML:**
```plantuml
class User {
    ' This is a user entity
    +name: String
    +email: String?
    +friends: List<User>
    +getFriendCount(): Int
}
```

**Generated Swift:**
```swift
/// This is a user entity
class User {
    var name: String
    var email: String?
    var friends: [User]

    func getFriendCount() -> Int {
        // TODO: implement
    }
}
```

**PlantUML:**
```plantuml
class Repository<T> {
    ' Generic repository class
    +items: List<T> // collection of items
    +addItem(item: T, index: Int): Void
    +findItem(predicate: (T) -> Bool): T?
}
```

**Generated Swift:**
```swift
/// Generic repository class
class Repository<T> {
    var items: [T] // collection of items

    func addItem(item: T, index: Int) -> Void {
        // TODO: implement
    }

    func findItem(predicate: (T) -> Bool) -> T? {
        // TODO: implement
    }
}
```

## Roadmap

- TypeScript, Kotlin, Java support ("puml2any")
- Inheritance, protocol, and association mapping
- XMI/UML import, cross-UML support

## Contributing

Pull requests and issues welcome!

## Pull Request Guidelines

- Use English for all code comments and commit messages.  
- Add/modify tests when submitting new features.  
- Briefly describe your changes in the PR description.