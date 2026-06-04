import os
import re
import sys
import difflib
import subprocess
import tempfile
from sqlalchemy import create_engine, inspect, Table, Column, Integer, String, MetaData

# === AGENTS (CODE) ===
class CodeAnalyzer:
    def scan(self, root_path):
        files, langs = [], {}
        for root, _, filenames in os.walk(root_path):
            for fname in filenames:
                if fname.endswith(".py"):
                    files.append(os.path.join(root, fname))
                    langs[os.path.join(root, fname)] = "python"
                elif fname.endswith(".php"):
                    files.append(os.path.join(root, fname))
                    langs[os.path.join(root, fname)] = "php"
        return files, langs

class LegalAgent:
    def check(self, code, lang):
        issues = []
        if lang == "python" and ("eval(" in code or "exec(" in code):
            issues.append("Warning: Code uses eval/exec, which could break data/privacy laws.")
        elif lang == "php" and "eval(" in code:
            issues.append("Risk: eval() in PHP is not compliant for most business uses.")
        return issues

class CyberSecurityAgent:
    def scan(self, code, lang):
        flags = []
        if re.search(r'\braw_input\s*\(', code):
            flags.append("Unvalidated legacy input (raw_input) detected—could be risky.")
        if re.search(r'\binput\s*\(', code):
            flags.append("Unvalidated input detected—possible bug or hack risk.")
        if lang == "python" and re.search(r'password ?= ?[\'"]\w+[\'"]', code):
            flags.append("Hardcoded password found (security risk).")
        elif lang == "php":
            if "md5(" in code:
                flags.append("MD5 hashing is insecure. Should use a modern hashing library.")
            if "mysql_query(" in code:
                flags.append("Unprepared MySQL query detected—possible SQL injection risk.")
        return flags

class SelfHealingAgent:
    def heal(self, code, lang):
        issues = []
        if lang == "python":
            code = re.sub(r"(eval\s*\()", r"# BLOCKED: \1", code)
            if "# BLOCKED: eval(" in code:
                issues.append("Blocked eval() for security.")
            code = re.sub(r"(exec\s*\()", r"# BLOCKED: \1", code)
            if "# BLOCKED: exec(" in code:
                issues.append("Blocked exec() for security.")
        elif lang == "php":
            code = re.sub(r"(eval\s*\()", r"// BLOCKED: \1", code)
            if "// BLOCKED: eval(" in code:
                issues.append("Blocked eval() in PHP for security.")
        return code, issues

import ast, astor
class PrintModernizer(ast.NodeTransformer):
    def visit_Print(self, node):
        new_call = ast.Expr(value=ast.Call(
            func=ast.Name(id='print', ctx=ast.Load()),
            args=node.values, keywords=[]
        ))
        return ast.copy_location(new_call, node)

class UpgradeEngine:
    def upgrade(self, code, lang):
        changes = []
        upgraded = code
        if lang == "python":
            ast_success = True
            try:
                tree = ast.parse(code)
                tree = PrintModernizer().visit(tree)
                ast.fix_missing_locations(tree)
                upgraded = astor.to_source(tree)
                if upgraded != code:
                    changes.append("Modernized print statements using AST.")
            except Exception as e:
                ast_success = False
                try:
                    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w+', encoding='utf-8') as temp:
                        temp.write(code)
                        temp_path = temp.name
                    subprocess.run(
                        [sys.executable, "-m", "lib2to3", "-w", temp_path],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    with open(temp_path, "r", encoding='utf-8') as temp:
                        upgraded = temp.read()
                    os.remove(temp_path)
                    changes.append("Modernized print/raw_input using lib2to3 fallback.")
                except Exception as e:
                    changes.append(f"AST and 2to3 upgrades failed: {e}")
            upgraded, n = re.subn(r'\braw_input\b', 'input', upgraded)
            if n > 0:
                changes.append("Modernized input: replaced raw_input() with input().")
        elif lang == "php":
            orig = upgraded
            upgraded, n = re.subn(r'mysql_([a-z]+)', r'mysqli_\1', upgraded)
            if n > 0:
                changes.append(f"Updated {n} mysql_* functions to mysqli_* equivalents.")
        return upgraded, changes

# === REAL DBOpsAgent USING SQLAlchemy, FALLBACK TO SQLITE ===
class RealDBOpsAgent:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.metadata = MetaData()
    def safe_bootstrap(self, table_name="wicket_table"):
        with self.engine.connect() as conn:
            inspector = inspect(conn)
            if table_name not in inspector.get_table_names():
                print(f"⏳ Table {table_name} not found; bootstrapping for zero-config demo...")
                Table(table_name, self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('name', String))
                self.metadata.create_all(self.engine)
                print(f"✅ Table {table_name} created (columns: id, name).")
    def index_check(self, table_name):
        with self.engine.connect() as conn:
            inspector = inspect(conn)
            indexes = inspector.get_indexes(table_name)
            if not indexes:
                print(f"⚠️ No indexes found on table {table_name}. Recommend optimization.")
            else:
                print(f"Indexes on {table_name}:", [i['name'] for i in indexes])
    def schema_drift_check(self, required_columns, table_name):
        with self.engine.connect() as conn:
            inspector = inspect(conn)
            actual_columns = [col['name'] for col in inspector.get_columns(table_name)]
            missing_cols = [c for c in required_columns if c not in actual_columns]
            if missing_cols:
                print(f"⚠️ Schema drift: {table_name} missing columns {missing_cols}.")
            else:
                print(f"Schema matches for {table_name}.")
    def run_all(self, table_name="wicket_table"):
        print("\n--- Wicket Sky DB Agent ---")
        self.safe_bootstrap(table_name)
        try:
            self.index_check(table_name)
            self.schema_drift_check(["id", "name"], table_name)
        except Exception as e:
            print("DB health check failed:", e)

# === SYNTAX CHECKS ===
def syntax_check_python(code):
    try:
        compile(code, '<string>', 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
def syntax_check_php(code):
    with tempfile.NamedTemporaryFile(suffix='.php', delete=False, mode='w+', encoding='utf-8') as temp:
        temp.write(code)
        temp_path = temp.name
    proc = subprocess.run(["php", "-l", temp_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.remove(temp_path)
    if proc.returncode == 0:
        return True, ""
    else:
        return False, proc.stdout.decode('utf-8') + proc.stderr.decode('utf-8')

# === REPORTING ===
def plain_english_report(fname, lang, pre_changes, pre_issues, pre_legal, pre_cyber, post_changes, post_issues, post_legal, post_cyber, before, after):
    lines = []
    lines.append(f"\n--- Sky Bridge Report for: {os.path.basename(fname)} ({lang.upper()}) ---")
    if pre_changes or pre_issues or pre_legal or pre_cyber:
        lines.append("Before upgrade:")
        if pre_changes: lines.append(" Upgrade/Migration suggestions:"); lines.extend([f"  - {c}" for c in pre_changes])
        if pre_issues: lines.append(" Healing required:"); lines.extend([f"  - {i}" for i in pre_issues])
        if pre_legal: lines.append(" Legal/Compliance:"); lines.extend([f"  - {l}" for l in pre_legal])
        if pre_cyber: lines.append(" Cybersecurity:"); lines.extend([f"  - {s}" for s in pre_cyber])
    lines.append("\nAfter upgrade & healing:")
    if post_changes: lines.append(" Upgrade:"); lines.extend([f"  - {c}" for c in post_changes])
    if post_issues: lines.append(" Healed:"); lines.extend([f"  - {i}" for i in post_issues])
    if post_legal: lines.append(" Legal/Compliance:"); lines.extend([f"  - {l}" for l in post_legal])
    if post_cyber: lines.append(" Cybersecurity:"); lines.extend([f"  - {s}" for s in post_cyber])
    if not post_changes and not post_issues and not post_legal and not post_cyber:
        lines.append("No problems or risks found in upgraded code. Code is healthy and up to date.")
    lines.append("\nLegacy vs. Modernized Code (lines changed):")
    diff = list(difflib.unified_diff(
        before.strip().splitlines(), after.strip().splitlines(),
        fromfile="Legacy", tofile="Modern", lineterm=""
    ))
    lines.extend(diff)
    lines.append("\n" + "-"*60)
    print("\n".join(lines))

# === ENGINE RUNNER / ORCHESTRATOR ===
def main():
    print("=== Wicket Sky: Zero-Config Production-Grade Orchestrator ===")
    cwd = os.getcwd()
    analyzer = CodeAnalyzer()
    legal = LegalAgent()
    cyber = CyberSecurityAgent()
    healer = SelfHealingAgent()
    upgrader = UpgradeEngine()
    # Zero-config: Use SQLite fallback if env not set
    db_url = os.getenv("WICKET_DB_URL", default="sqlite:///ws_demo.db")
    dbops = RealDBOpsAgent(db_url)
    files, langs = analyzer.scan(cwd)
    if not files:
        print("No .py or .php legacy code found in this folder. Nothing to do! 🎉")
    else:
        for fname in files:
            with open(fname, encoding='utf-8') as f:
                code = f.read()
            lang = langs[fname]
            pre_legal_issues = legal.check(code, lang)
            pre_cyber_issues = cyber.scan(code, lang)
            pre_healed, pre_heal_report = healer.heal(code, lang)
            pre_changes = []
            pre_issues = pre_heal_report
            upgraded, changes = upgrader.upgrade(pre_healed, lang)
            # SAFETY: Syntax check
            syntax_ok, syntax_msg = True, ""
            if lang == "python":
                syntax_ok, syntax_msg = syntax_check_python(upgraded)
            if lang == "php":
                syntax_ok, syntax_msg = syntax_check_php(upgraded)
            if not syntax_ok:
                print(f"\n!!! WARNING: Healed/upgraded code in {fname} failed syntax check and was discarded for safety.")
                print(f"Error detail: {syntax_msg}")
                print("-" * 60)
                continue
            post_legal_issues = legal.check(upgraded, lang)
            post_cyber_issues = cyber.scan(upgraded, lang)
            post_healed, post_heal_report = healer.heal(upgraded, lang)
            plain_english_report(
                fname, lang,
                pre_changes, pre_issues, pre_legal_issues, pre_cyber_issues,
                changes, post_heal_report, post_legal_issues, post_cyber_issues,
                code, upgraded)
    dbops.run_all(table_name="wicket_table")
    print("\n✅ All code and ops agents complete. Wicket Sky PRODUCTION orchestrator finished.\n")

if __name__ == "__main__":
    main()