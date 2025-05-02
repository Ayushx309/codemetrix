# 🔍 CodeMetrix

<div align="center">

![CodeMetrix Banner](https://raw.githubusercontent.com/Ayushx309/codemetrix/main/assets/banner.svg)

> A sophisticated code analysis and cost estimation tool with advanced metrics

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Ayushx309/codemetrix?style=social)](https://github.com/Ayushx309/codemetrix/stargazers)
[![Follow](https://img.shields.io/github/followers/Ayushx309?style=social)](https://github.com/Ayushx309)



</div>

## ✨ Key Features

### 🎯 Advanced Static Analysis
- **Intelligent Code Metrics**
  - Advanced cyclomatic complexity calculation
  - AST-based code structure analysis
  - Smart pattern recognition for duplicates
  - Multi-language support (40+ languages)

- **Code Quality Assessment**
  - 🔄 Control Flow Analysis
  - 📝 Documentation Coverage Analysis
  - 🎯 Maintainability Scoring
  - 🔍 Duplicate Code Detection
  - 📊 Comprehensive Quality Metrics

### 💰 Advanced Cost Estimation
- **Industry-Standard Models**
  - COCOMO II (Constructive Cost Model)
  - Function Point Analysis
  - Calibrated LOC-based Estimation
  
- **Sophisticated Parameters**
  - Dynamic rate adjustment
  - Project complexity analysis
  - Team size optimization
  - Risk factor consideration

### 📊 Intelligent Reporting
- Rich interactive CLI interface
- Real-time analysis feedback
- Smart recommendations engine
- Detailed metric breakdowns
- Progress tracking
- Error resilience and recovery

## 🧮 Analysis Engine

CodeMetrix uses several sophisticated algorithms and techniques:

### Static Analysis
- Abstract Syntax Tree (AST) parsing
- Pattern matching algorithms
- Regex-based smart filtering
- Multi-pass code analysis

### Metrics Calculation
- Halstead complexity measures
- Maintainability index computation
- Documentation coverage analysis
- Duplicate code detection using hash comparison

### Cost Modeling
- COCOMO II algorithmic model
- Function Point Analysis (FPA)
- Calibrated estimation formulas
- Multi-factor adjustment system

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Ayushx309/codemetrix.git
cd codemetrix
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
python codemetrix.py -d /path/to/your/project
```

### Advanced Usage

```bash
# Analyze specific file types
python codemetrix.py -d /path/to/project -e py js ts

# Exclude comments and blank lines
python codemetrix.py -d /path/to/project --no-comments

# Custom hourly rate for cost estimation
python codemetrix.py -d /path/to/project -r 75

# Exclude specific directories
python codemetrix.py -d /path/to/project -x node_modules venv
```

## 📖 Documentation

### Command Line Options

| Option | Description |
|--------|-------------|
| `-d, --directory` | Directory to analyze (interactive if not specified) |
| `-e, --extensions` | File extensions to include (default: common code files) |
| `-a, --all` | Include blank lines in the count |
| `-c, --no-comments` | Exclude comment lines from the count |
| `-x, --exclude` | Directories to exclude from analysis |
| `-r, --rate` | Hourly rate in USD for cost estimation |
| `--no-cost` | Skip cost estimation |

### Supported Languages

<details>
<summary>Click to expand language list</summary>

#### Web Technologies
- HTML/CSS: `.html`, `.htm`, `.css`, `.scss`, `.sass`, `.less`
- JavaScript: `.js`, `.jsx`, `.ts`, `.tsx`, `.vue`, `.svelte`

#### Backend Languages
- Python: `.py`
- Java: `.java`
- PHP: `.php`
- Ruby: `.rb`
- Go: `.go`
- Rust: `.rs`
- C#: `.cs`

#### Systems Programming
- C/C++: `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`
- Objective-C: `.m`, `.mm`

#### Mobile Development
- Swift: `.swift`
- Kotlin: `.kt`
- Dart: `.dart`

#### Configuration & Data
- SQL: `.sql`
- JSON: `.json`
- YAML: `.yaml`, `.yml`
- TOML: `.toml`
- XML: `.xml`
</details>

## 📊 Metrics Explained

### Code Quality Metrics

1. **Cyclomatic Complexity**
   - Measures code complexity based on control flow
   - Lower scores indicate simpler, more maintainable code
   - Target: < 10 for good maintainability

2. **Documentation Coverage**
   - Percentage of documented functions and classes
   - Higher scores indicate better documentation
   - Target: > 70% for good documentation

3. **Maintainability Index**
   - Composite metric of code maintainability
   - Scale: 0-100 (higher is better)
   - Ratings:
     - 🟢 85-100: Excellent
     - 🟡 65-84: Good
     - 🟠 40-64: Fair
     - 🔴 0-39: Poor

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Rich library for beautiful CLI formatting
- COCOMO II model research papers
- Function Point Analysis methodology

## Author

**Ayush**
- GitHub: [@Ayushx309](https://github.com/Ayushx309)
- Website: [eternalbytes.in](https://eternalbytes.in/)
- Location: Ahmedabad, Gujarat, India

---
<div align="center">
Made with ❤️ by <a href="https://github.com/Ayushx309">Ayush</a> at <a href="https://eternalbytes.in">Eternal Bytes</a>

⭐️ Star this project if you find it useful!
</div> 
