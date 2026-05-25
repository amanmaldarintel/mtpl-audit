import re
import os
from datetime import datetime
from collections import defaultdict

mtpl_file = r"J:\engineering\dev\user_links\mnaing\DMR_PO_TP\ShortTP\WW20p2_S620_P47_IDI\Modules\FUN_CORE_CBB\FUN_CORE_CBB.mtpl"
output_file = "FUN_CORE_CBB_SBFT_audit_report.html"

is_uccx1 = "UCCX1" in mtpl_file.upper()
is_uccx1 = True

print("Parsing MTPL file for SBFT instances...")
print(f"Is UCCX1 variant: {is_uccx1}")

instances = []
counters_count = 0
state = "IDLE"
current_instance = None
brace_count = 0
abbreviation_map = {}

with open(mtpl_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

in_counters = False
counter_brace_count = 0

for line_num, line in enumerate(lines, 1):
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        continue
    if stripped.startswith("Counters"):
        in_counters = True
        counter_brace_count = 0
        continue
    if in_counters:
        counter_brace_count += stripped.count("{") - stripped.count("}")
        if "{" in stripped:
            continue
        if "}" in stripped and counter_brace_count == 0:
            in_counters = False
            continue
        if "," in stripped or stripped.endswith("_0"):
            counters_count += 1
        continue
    if state == "IDLE":
        # Try format: "TestType Method InstanceName" or "TestType InstanceName"
        match = re.match(r"(CSharpTest|MultiTrialTest)\s+(.+)", stripped)
        if match:
            test_type = match.group(1)
            rest = match.group(2).strip()

            # Check if it's "Method InstanceName" format (has space and doesn't end with {)
            parts = rest.split(None, 1)  # Split on first whitespace
            if len(parts) == 2 and not parts[1].startswith('{'):
                # Format: TestType Method InstanceName
                test_method = parts[0]
                instance_name = parts[1]
            else:
                # Format: TestType InstanceName (MultiTrialTest case)
                test_method = test_type  # Use test type as method
                instance_name = parts[0] if parts else rest

            current_instance = {
                "name": instance_name,
                "type": test_type,
                "method": test_method,
                "line": line_num,
                "parameters": {}
            }
            state = "IN_INSTANCE"
            brace_count = 0
            continue
    if state == "IN_INSTANCE":
        brace_count += stripped.count("{") - stripped.count("}")
        if "{" in stripped:
            continue
        if "}" in stripped and brace_count == 0:
            if current_instance:
                instances.append(current_instance)
                current_instance = None
            state = "IDLE"
            continue
        if "=" in stripped:
            cleaned = stripped.rstrip(";").strip()
            parts = cleaned.split("=", 1)
            if len(parts) == 2:
                param_name = parts[0].strip()
                param_value = parts[1].strip().strip('"')

                # Handle "TrialParam ParameterName" format (F5+ frequencies)
                # Remove "TrialParam " prefix from parameter name if present
                param_name = re.sub(r'^\s*TrialParam\s+', '', param_name, flags=re.IGNORECASE)

                current_instance["parameters"][param_name] = param_value

sbft_instances = [inst for inst in instances if "SBFT" in inst["name"] and "IDIBIST" not in inst["name"]]

print(f"Total instances: {len(instances)}")
print(f"SBFT instances (excluding IDIBIST): {len(sbft_instances)}")
print(f"Counters: {counters_count}")

def remove_comments(value):
    """Remove # and everything after"""
    if value == "N/A" or not value:
        return value
    return re.sub(r'#.*$', '', value).strip()

def highlight_keywords(text):
    """Highlight ALL keywords with comprehensive color coding - case insensitive, embedded matching"""
    if not text or text == "N/A":
        return text

    # Test Types - Bold (match embedded occurrences too)
    text = re.sub(r'(SRH)', r'<span class="kw-srh">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(CHK)', r'<span class="kw-chk">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(VMAX)', r'<span class="kw-vmax">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(LTTC)', r'<span class="kw-lttc">\1</span>', text, flags=re.IGNORECASE)

    # Signal States - Bold Italic/Bold
    text = re.sub(r'(SIGOFF)', r'<span class="kw-sigoff">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(SIGON)', r'<span class="kw-sigon">\1</span>', text, flags=re.IGNORECASE)

    # Instruction Sets / Corners - Bold (AVX3 before AVX2!)
    text = re.sub(r'(AVX3)', r'<span class="kw-avx3">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(AVX2)', r'<span class="kw-avx2">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(AMX)', r'<span class="kw-amx">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(SSE)', r'<span class="kw-sse">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(TMUL)', r'<span class="kw-tmul">\1</span>', text, flags=re.IGNORECASE)

    # Cache Types - Bold (specific order: longer matches first)
    text = re.sub(r'(DRGMLC)', r'<span class="kw-cache">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(MLCFG)', r'<span class="kw-cache">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(DRGLLC)', r'<span class="kw-cache">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(LLCFG)', r'<span class="kw-cache">\1</span>', text, flags=re.IGNORECASE)
    # Don't match MLC/LLC/DRG if already matched above
    if '<span class="kw-cache">' not in text:
        text = re.sub(r'(MLC)', r'<span class="kw-cache">\1</span>', text, flags=re.IGNORECASE)
        text = re.sub(r'(LLC)', r'<span class="kw-cache">\1</span>', text, flags=re.IGNORECASE)
        text = re.sub(r'(DRG)', r'<span class="kw-cache">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(SLC)', r'<span class="kw-cache">\1</span>', text, flags=re.IGNORECASE)

    # Frequencies - Bold
    text = re.sub(r'(F[1-7])', r'<span class="kw-freq">\1</span>', text, flags=re.IGNORECASE)

    # IA must be done carefully to avoid matching in words like "via", "special" etc.
    # Only match _IA_ or IA at word boundaries or start/end
    text = re.sub(r'(^IA|_IA_|_IA$|^IA_)', r'<span class="kw-ia">\1</span>', text, flags=re.IGNORECASE)

    return text

def parse_die_value(value, for_abbreviation=False):
    """
    Universal DIE parser for BypassPort, MaskBuilderSettings, DecoderConfiguration

    Standard Templates:
    Template 1: DIE(<uccx1_value>, <uccap_value>, <dont_care>, <dont_care>)
    Template 2: DIE(QUAL(<qa>, <classhot>), <uccap_value>, <dont_care>, <dont_care>)

    Note: In Template 2, qa value comes FIRST, classhot value comes SECOND in QUAL tuple
    """
    if value == "N/A" or not value:
        return "N/A"

    # Remove comments
    value = remove_comments(value)
    
    # Simple value (not DIE)
    if 'DIE' not in value and 'QUAL' not in value:
        if for_abbreviation:
            abbreviated = re.sub(r'^IP_CBB::IP_CBB_BASE::', '', value)
            abbreviated = re.sub(r'^VminVars\.', '', abbreviated)
            return abbreviated
        return value
    
    # Check for QUAL pattern (StartVoltages)
    qual_match = re.search(r'QUAL\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', value)
    if qual_match:
        # QUAL has two string parameters
        # For UCCX1: use 1st, For UCCX4: use 2nd
        param1 = qual_match.group(1)
        param2 = qual_match.group(2)
        selected = param1 if is_uccx1 else param2
        
        if for_abbreviation:
            selected = re.sub(r'^DUT\.', '', selected)
        return selected
    
    # Check for standalone DOWNSTREAM_SOCKETS or QUAL
    standalone_match = re.search(r'(?:DOWNSTREAM_SOCKETS|QUAL(?:_TYPE)?)\s*\(([^)]+)\)', value)
    if standalone_match and 'DIE' not in value:
        params = [p.strip() for p in standalone_match.group(1).split(',')]
        if is_uccx1:
            return params[0] if params else "N/A"
        else:
            return params[1] if len(params) > 1 else params[0] if params else "N/A"
    
    # Parse DIE(...)
    die_match = re.search(r'DIE\s*\((.*)\)', value, re.DOTALL)
    if not die_match:
        return value
    
    die_content = die_match.group(1)
    
    # Check for nested patterns
    patterns = re.findall(r'(?:DOWNSTREAM_SOCKETS|QUAL(?:_TYPE)?)\s*\([^)]+\)', die_content)
    
    if patterns:
        selected_pattern = patterns[0] if is_uccx1 else (patterns[1] if len(patterns) > 1 else patterns[0])
        value_match = re.search(r'\(([^)]+)\)', selected_pattern)
        if value_match:
            params = [p.strip() for p in value_match.group(1).split(',')]
            if is_uccx1:
                return params[0] if params else "N/A"
            else:
                return params[1] if len(params) > 1 else (params[0] if params else "N/A")
    
    # Split DIE content by comma (respecting nested structures)
    values = []
    depth = 0
    current = ""
    for char in die_content:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ',' and depth == 0:
            values.append(current.strip())
            current = ""
            continue
        current += char
    if current:
        values.append(current.strip())
    
    # Select value based on variant
    if is_uccx1:
        selected_value = values[0] if values else "N/A"
    else:
        selected_value = values[1] if len(values) > 1 else (values[0] if values else "N/A")
    
    # Abbreviate if needed
    if for_abbreviation and selected_value != "N/A":
        selected_value = re.sub(r'^IP_CBB::IP_CBB_BASE::', '', selected_value)
        selected_value = re.sub(r'^VminVars\.', '', selected_value)
        selected_value = re.sub(r'^DUT\.', '', selected_value)
        selected_value = re.sub(r'^"([^"]+)"$', r'\1', selected_value)  # Remove quotes
    
    return selected_value

def abbreviate_value(value, param_name=""):
    """Abbreviate long values and track in abbreviation_map"""
    if value == "N/A" or not value:
        return value
    
    # Remove comments first
    value = remove_comments(value)
    
    # For MaskBuilderSettings, DecoderConfiguration, StartVoltages - use parse_die_value
    if param_name in ["MaskBuilderSettings", "DecoderConfiguration", "StartVoltages"]:
        abbreviated = parse_die_value(value, for_abbreviation=True)
        if abbreviated != value and abbreviated != "N/A":
            abbreviation_map[abbreviated] = value
        return abbreviated
    
    original = value
    abbreviated = value
    
    abbreviated = re.sub(r'^IP_CBB::IP_CBB_BASE::', '', abbreviated)
    abbreviated = re.sub(r'^SharedStorage\.', '', abbreviated)
    
    if param_name in ["VoltageTargets", "StepSize"]:
        abbreviated = re.sub(r'^VminVars\.', '', abbreviated)
    
    if original != abbreviated:
        abbreviation_map[abbreviated] = original
    
    return abbreviated

def parse_setpoints_preinstance(value):
    """
    Parse SetPointsPreInstance into components with proper formatting

    Handles two cases:
    1. Usual format: SetPointsPreInstance = IP_CBB::IP_CBB_BASE::RatioVars.RATIOSETUP_...
    2. TrialParam format (F5+): TrialParam SetPointsPreInstance = "RST:CORE:"+FlowMatrix...

    CRITICAL: Remove "TrialParam " prefix if present before parsing
    """
    components = {
        "RATIOSETUP": "N/A",
        "THR": "N/A",
        "AVX_LICENSE": "N/A",
        "DSC": "N/A",
        "IFPMIA": "N/A",
        "LS": "N/A",
        "THR_LLC": "N/A",
        "CYCLE": "N/A"
    }

    if value == "N/A" or not value:
        return components

    # Remove "TrialParam " prefix if present (for F5+ frequencies)
    value = re.sub(r'^\s*TrialParam\s+', '', value, flags=re.IGNORECASE)

    ratio_match = re.search(r"RATIOSETUP_[\w_]+", value)
    if ratio_match:
        components["RATIOSETUP"] = ratio_match.group(0)
    
    dsc_match = re.search(r'FUN:(DSC\w+):"?\s*\+\s*([^\s+,]+)', value)
    if dsc_match:
        dsc_key = dsc_match.group(1)
        dsc_val = dsc_match.group(2)
        var_match = re.search(r'[\w_]+\.([\w_]+)', dsc_val)
        if var_match:
            components["DSC"] = f"{dsc_key}:{var_match.group(1)}"
        else:
            clean_val = dsc_val.strip().strip('"').strip()
            components["DSC"] = f"{dsc_key}:{clean_val}"
    
    ifpmia_match = re.search(r'FUN:IFPMIA:"?\s*\+\s*([^\s+,]+)', value)
    if ifpmia_match:
        ifpmia_val = ifpmia_match.group(1)
        var_match = re.search(r'[\w_]+\.([\w_]+)', ifpmia_val)
        if var_match:
            components["IFPMIA"] = f"IFPMIA:{var_match.group(1)}"
        else:
            clean_val = ifpmia_val.strip().strip('"').strip()
            components["IFPMIA"] = f"IFPMIA:{clean_val}"
    
    simple_patterns = re.findall(r'FUN:(\w+):([^",+\s]+)', value)
    for key, val in simple_patterns:
        if key in ["THR", "AVX_LICENSE", "LS", "THR_LLC", "CYCLE"]:
            clean_val = val.strip().strip('"').strip()
            components[key] = clean_val
    
    return components

def categorize_instance(inst):
    """Categorize test instance by type"""
    name = inst["name"]
    
    test_type = "Other"
    if "SRH" in name:
        test_type = "SRH"
    elif "CHK" in name:
        test_type = "CHK"
    elif "VMAX" in name:
        test_type = "VMAX"
    elif "LTTC" in name:
        test_type = "LTTC"
    
    freq = "N/A"
    freq_match = re.search(r"F(\d+)", name)
    if freq_match:
        freq_num = int(freq_match.group(1))
        freq = f"F{freq_num}"
    else:
        freq_num = 99
    
    cache = "N/A"
    if "DRGMLC" in name:
        cache = "DRGMLC"
    elif "MLCFG" in name:
        cache = "MLCFG"
    elif "DRGLLC" in name:
        cache = "DRGLLC"
    elif "LLCFG" in name:
        cache = "LLCFG"
    elif "MLC" in name:
        cache = "MLC"
    elif "SLC" in name:
        cache = "SLC"
    elif "DRG" in name:
        cache = "DRG"
    elif "LLC" in name:
        cache = "LLC"
    
    instr_set = "N/A"
    if "TMUL" in name:
        instr_set = "TMUL"
    elif "AVX3" in name:
        instr_set = "AVX3"
    elif "AVX2" in name:
        instr_set = "AVX2"
    elif "AMX" in name:
        instr_set = "AMX"
    elif "SSE" in name:
        instr_set = "SSE"
    elif "_IA_" in name or "CBBIA" in name:
        instr_set = "IA"
    
    sig_state = "N/A"
    if "SIGON" in name:
        sig_state = "SIGON"
    elif "SIGOFF" in name:
        sig_state = "SIGOFF"
    
    return {
        "test_type": test_type,
        "frequency": freq,
        "freq_num": freq_num,
        "cache": cache,
        "instr_set": instr_set,
        "sig_state": sig_state
    }

test_type_order = {"SRH": 1, "CHK": 2, "VMAX": 3, "LTTC": 4, "Other": 99}
corner_order = {"IA": 1, "AVX2": 2, "AVX3": 3, "AMX": 4, "SSE": 5, "TMUL": 6, "N/A": 99}
cache_order = {"DRGMLC": 1, "MLCFG": 2, "DRGLLC": 3, "LLCFG": 4, "DRG": 5, "MLC": 6, "SLC": 7, "LLC": 8, "N/A": 99}

grouped = defaultdict(list)
for inst in sbft_instances:
    cat = categorize_instance(inst)
    group_key = f"{cat['test_type']} {cat['frequency']} - {cat['instr_set']} - {cat['cache']}"
    grouped[group_key].append((inst, cat))

def sort_key(item):
    group_name, instances = item
    if instances:
        cat = instances[0][1]
        return (
            test_type_order.get(cat['test_type'], 99),
            cat['freq_num'],
            corner_order.get(cat['instr_set'], 99),
            cache_order.get(cat['cache'], 99),
            group_name
        )
    return (99, 99, 99, 99, group_name)

sorted_groups = sorted(grouped.items(), key=sort_key)

print(f"Grouped into {len(grouped)} categories")

vmin_count = sum(1 for i in sbft_instances if i["method"] == "VminSearchPlus")
csharp_count = sum(1 for i in sbft_instances if i["type"] == "CSharpTest")
multitrial_count = sum(1 for i in sbft_instances if i["type"] == "MultiTrialTest")

print(f"VminSearchPlus: {vmin_count}, CSharpTest: {csharp_count}, MultiTrialTest: {multitrial_count}")
print("Generating HTML report...")

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
filename = os.path.basename(mtpl_file)

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MTPL SBFT Audit - {filename}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; min-height: 100vh; }}
.container {{ max-width: 98%; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
header h1 {{ font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
header p {{ font-size: 1em; opacity: 0.9; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; padding: 30px; background: #f8f9fa; }}
.stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; border-left: 4px solid #667eea; transition: transform 0.3s; }}
.stat-card:hover {{ transform: translateY(-5px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }}
.stat-card h3 {{ font-size: 2em; color: #667eea; margin-bottom: 10px; }}
.stat-card p {{ color: #666; font-size: 0.9em; }}
.tabs {{ display: flex; background: #e9ecef; overflow-x: auto; flex-wrap: wrap; }}
.tab-button {{ flex: 1; min-width: 140px; padding: 15px 10px; background: #e9ecef; border: none; cursor: pointer; font-size: 0.95em; font-weight: 600; color: #495057; transition: all 0.3s; border-bottom: 3px solid transparent; }}
.tab-button:hover {{ background: #dee2e6; }}
.tab-button.active {{ background: white; color: #667eea; border-bottom: 3px solid #667eea; }}
.tab-content {{ display: none; padding: 30px; }}
.tab-content.active {{ display: block; animation: fadeIn 0.5s; }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th {{ background: #4a5568; color: white; padding: 10px 6px; text-align: left; font-weight: 600; position: sticky; top: 0; font-size: 0.9em; z-index: 10; user-select: text; border-right: 2px solid #2d3748; }}
th .resizer {{ position: absolute; top: 0; right: 0; width: 5px; height: 100%; cursor: col-resize; user-select: none; }}
th .resizer:hover {{ background: #667eea; }}
td {{ padding: 6px; border-bottom: 1px solid #e9ecef; font-size: 0.95em; border-right: 1px solid #e9ecef; }}
td.wrap-text {{ white-space: normal; word-wrap: break-word; }}
td.no-wrap {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
tr:nth-child(even) {{ background: #f8f9fa; }}
tr:hover {{ background: #e7f3ff; }}
.na {{ color: #999; font-style: italic; }}

/* Keyword Highlighting - Test Types */
.kw-srh {{ color: #28a745; font-weight: bold; }}
.kw-chk {{ color: #007bff; font-weight: bold; }}
.kw-vmax {{ color: #dc3545; font-weight: bold; }}
.kw-lttc {{ color: #17a2b8; font-weight: bold; }}

/* Keyword Highlighting - Signal States */
.kw-sigoff {{ color: #e83e8c; font-weight: bold; font-style: italic; }}
.kw-sigon {{ color: #6610f2; font-weight: bold; }}

/* Keyword Highlighting - Instruction Sets / Corners */
.kw-avx2 {{ color: #fd7e14; font-weight: bold; }}
.kw-avx3 {{ color: #20c997; font-weight: bold; }}
.kw-amx {{ color: #6f42c1; font-weight: bold; }}
.kw-sse {{ color: #e83e8c; font-weight: bold; }}
.kw-tmul {{ color: #fd7e14; font-weight: bold; }}
.kw-ia {{ color: #17a2b8; font-weight: bold; }}

/* Keyword Highlighting - Cache Types */
.kw-cache {{ color: #6c757d; font-weight: bold; }}

/* Keyword Highlighting - Frequencies */
.kw-freq {{ color: #007bff; font-weight: bold; }}

/* Signal column formatting */
.sig-sigoff {{ color: #e83e8c; font-weight: bold; font-style: italic; }}
.sig-sigon {{ color: #6610f2; font-weight: bold; }}

.group-header
.test-type-SRH {{ color: #28a745; font-weight: bold; }}
.test-type-CHK {{ color: #007bff; font-weight: bold; }}
.test-type-VMAX {{ color: #dc3545; font-weight: bold; }}
.test-type-LTTC {{ color: #17a2b8; font-weight: bold; }}
.table-container {{ overflow-x: auto; max-height: 700px; overflow-y: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.search-box {{ margin-bottom: 20px; padding: 10px; width: 100%; max-width: 400px; border: 2px solid #667eea; border-radius: 6px; font-size: 1em; }}
.note {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px; border-radius: 4px; }}
.note strong {{ color: #856404; }}
.filter-controls {{ background: #e7f3ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #007bff; display: flex; flex-wrap: wrap; gap: 15px; align-items: center; }}
.filter-controls label {{ display: inline-flex; align-items: center; font-weight: 600; color: #495057; cursor: pointer; }}
.filter-controls input[type="checkbox"] {{ margin-right: 8px; width: 18px; height: 18px; cursor: pointer; }}
.filter-controls select {{ padding: 8px; border: 2px solid #667eea; border-radius: 4px; font-size: 0.95em; cursor: pointer; }}
.hidden-row {{ display: none !important; }}
.hidden-col {{ display: none !important; }}
.abbrev-table {{ margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
.abbrev-table h3 {{ color: #1e3c72; margin-bottom: 15px; }}
.abbrev-table table {{ font-size: 0.85em; }}
.abbrev-table th {{ background: #6c757d; }}
.font-small {{ font-size: 0.75em !important; }}
.font-medium {{ font-size: 0.9em !important; }}
.font-large {{ font-size: 1.1em !important; }}
.bypass-port-col {{ }}
</style>
</head>
<body>
<div class="container">
<header>
<h1>🔍 MTPL SBFT Audit Report</h1>
<p><strong>File:</strong> {filename}</p>
<p><strong>Generated:</strong> {timestamp}</p>
<p><strong>Variant:</strong> {"UCCX1" if is_uccx1 else "UCCX4"}</p>
</header>

<section class="summary">
<div class="stat-card"><h3>{len(sbft_instances)}</h3><p>SBFT Instances</p></div>
<div class="stat-card"><h3>{vmin_count}</h3><p>VminSearchPlus</p></div>
<div class="stat-card"><h3>{len(grouped)}</h3><p>Groups</p></div>
<div class="stat-card"><h3>{counters_count}</h3><p>Total Counters</p></div>
</section>

<section class="tabs">
<button class="tab-button active" onclick="openTab(event, 'tab1')">📋 Overview</button>
<button class="tab-button" onclick="openTab(event, 'tab2')">⚙️ SetPoints Detail</button>
<button class="tab-button" onclick="openTab(event, 'tab3')">⚡ Voltage & Timing</button>
<button class="tab-button" onclick="openTab(event, 'tab4')">🎭 Mask & Pattern</button>
<button class="tab-button" onclick="openTab(event, 'tab5')">📖 Abbreviations</button>
</section>

<div id="tab1" class="tab-content active">
<h2>SBFT Instance Overview</h2>
<div class="note">
<strong>Keywords:</strong> 
<span class="kw-srh">SRH</span> <span class="kw-chk">CHK</span> <span class="kw-vmax">VMAX</span> <span class="kw-lttc">LTTC</span> | 
<span class="kw-sigoff">SIGOFF</span> <span class="kw-sigon">SIGON</span> | 
<span class="kw-avx2">AVX2</span> <span class="kw-avx3">AVX3</span> <span class="kw-amx">AMX</span> <span class="kw-sse">SSE</span> <span class="kw-ia">IA</span> <span class="kw-tmul">TMUL</span> | 
<span class="kw-cache">Cache</span> <span class="kw-freq">F1-F7</span>
</div>
<div class="filter-controls">
<label><input type="checkbox" id="hideBypassPort1_tab1" onchange="toggleBypassPort('table1')"> Hide BypassPort = 1</label>
<label><input type="checkbox" id="hideBypassPortCol_tab1" onchange="toggleBypassPortCol('table1')"> Hide BypassPort Column</label>
<label><input type="checkbox" id="wrapText_tab1" onchange="toggleTextWrap('table1')"> Enable Text Wrapping</label>
<label>Font Size: 
<select id="fontSize_tab1" onchange="changeFontSize('table1', this.value)">
<option value="small">Small</option>
<option value="medium" selected>Medium</option>
<option value="large">Large</option>
</select>
</label>
</div>
<input type="text" class="search-box" id="search1" onkeyup="searchTable('search1', 'table1')" placeholder="Search instances...">
<div class="table-container">
<table id="table1">
<thead><tr>
<th><div class="resizer" data-table="table1"></div>#</th>
<th><div class="resizer" data-table="table1"></div>Instance Name</th>
<th><div class="resizer" data-table="table1"></div>Type</th>
<th><div class="resizer" data-table="table1"></div>Freq</th>
<th><div class="resizer" data-table="table1"></div>Corner</th>
<th><div class="resizer" data-table="table1"></div>Cache</th>
<th><div class="resizer" data-table="table1"></div>Signal</th>
<th class="bypass-port-col"><div class="resizer" data-table="table1"></div>BypassPort</th>
<th><div class="resizer" data-table="table1"></div>Patlist</th>
</tr></thead>
<tbody>
"""

idx = 1
for group_name, group_instances in sorted_groups:
    html += f'<tr class="group-header"><td colspan="9">📁 {group_name} ({len(group_instances)} instances)</td></tr>'
    
    for inst, cat in group_instances:
        test_type_class = f"test-type-{cat['test_type']}"
        patlist = remove_comments(inst["parameters"].get("Patlist", "N/A"))
        patlist_highlighted = highlight_keywords(patlist)
        bypass_port = parse_die_value(inst["parameters"].get("BypassPort", "N/A"))

        sig_class = ""
        if cat["sig_state"] == "SIGOFF":
            sig_class = "sig-sigoff"
        elif cat["sig_state"] == "SIGON":
            sig_class = "sig-sigon"

        html += f"""<tr data-bypass="{bypass_port}">
<td class="no-wrap">{idx}</td>
<td class="no-wrap"><strong>{highlight_keywords(inst["name"])}</strong></td>
<td class="{test_type_class} no-wrap">{highlight_keywords(cat["test_type"])}</td>
<td class="no-wrap">{highlight_keywords(cat["frequency"])}</td>
<td class="no-wrap">{highlight_keywords(cat["instr_set"])}</td>
<td class="no-wrap">{highlight_keywords(cat["cache"])}</td>
<td class="{sig_class} no-wrap">{highlight_keywords(cat["sig_state"])}</td>
<td class="bypass-port-col no-wrap">{bypass_port}</td>
<td class="no-wrap" title="{patlist}">{patlist_highlighted}</td>
</tr>
"""
        idx += 1

html += """</tbody></table></div></div>

<div id="tab2" class="tab-content">
<h2>⚙️ SetPointsPreInstance Deep Dive</h2>
<div class="filter-controls">
<label><input type="checkbox" id="hideBypassPort1_tab2" onchange="toggleBypassPort('table2')"> Hide BypassPort = 1</label>
<label><input type="checkbox" id="hideBypassPortCol_tab2" onchange="toggleBypassPortCol('table2')"> Hide BypassPort Column</label>
<label><input type="checkbox" id="hideRawValue_tab2" onchange="toggleRawValue()"> Hide Raw Value</label>
<label><input type="checkbox" id="wrapText_tab2" onchange="toggleTextWrap('table2')"> Enable Text Wrapping</label>
<label>Font Size: 
<select id="fontSize_tab2" onchange="changeFontSize('table2', this.value)">
<option value="small">Small</option>
<option value="medium" selected>Medium</option>
<option value="large">Large</option>
</select>
</label>
</div>
<input type="text" class="search-box" id="search2" onkeyup="searchTable('search2', 'table2')" placeholder="Search...">
<div class="table-container">
<table id="table2">
<thead><tr>
<th><div class="resizer" data-table="table2"></div>#</th>
<th><div class="resizer" data-table="table2"></div>Instance</th>
<th><div class="resizer" data-table="table2"></div>Type</th>
<th><div class="resizer" data-table="table2"></div>Freq</th>
<th><div class="resizer" data-table="table2"></div>Corner</th>
<th><div class="resizer" data-table="table2"></div>RATIOSETUP</th>
<th><div class="resizer" data-table="table2"></div>THR</th>
<th><div class="resizer" data-table="table2"></div>AVX_LIC</th>
<th><div class="resizer" data-table="table2"></div>DSC</th>
<th><div class="resizer" data-table="table2"></div>IFPMIA</th>
<th><div class="resizer" data-table="table2"></div>LS</th>
<th><div class="resizer" data-table="table2"></div>CYCLE</th>
<th class="bypass-port-col"><div class="resizer" data-table="table2"></div>BypassPort</th>
<th class="raw-value-col"><div class="resizer" data-table="table2"></div>Raw Value</th>
</tr></thead>
<tbody>
"""

idx = 1
for group_name, group_instances in sorted_groups:
    html += f'<tr class="group-header"><td colspan="14">📁 {group_name}</td></tr>'

    for inst, cat in group_instances:
        setpoints_raw = inst["parameters"].get("SetPointsPreInstance", "N/A")
        sp = parse_setpoints_preinstance(setpoints_raw)
        bypass_port = parse_die_value(inst["parameters"].get("BypassPort", "N/A"))

        html += f"""<tr data-bypass="{bypass_port}">
<td class="no-wrap">{idx}</td>
<td class="no-wrap" title="{inst['name']}"><strong>{highlight_keywords(inst["name"])}</strong></td>
<td class="{f'test-type-{cat["test_type"]}' if cat['test_type'] != 'N/A' else ''} no-wrap">{highlight_keywords(cat["test_type"])}</td>
<td class="no-wrap">{highlight_keywords(cat["frequency"])}</td>
<td class="no-wrap">{highlight_keywords(cat["instr_set"])}</td>
<td class="{'na' if sp['RATIOSETUP'] == 'N/A' else ''} no-wrap" title="{sp['RATIOSETUP']}">{highlight_keywords(sp["RATIOSETUP"])}</td>
<td class="{'na' if sp['THR'] == 'N/A' else ''} no-wrap">{highlight_keywords(sp["THR"])}</td>
<td class="{'na' if sp['AVX_LICENSE'] == 'N/A' else ''} no-wrap">{highlight_keywords(sp["AVX_LICENSE"])}</td>
<td class="{'na' if sp['DSC'] == 'N/A' else ''} no-wrap" title="{sp['DSC']}">{highlight_keywords(sp["DSC"])}</td>
<td class="{'na' if sp['IFPMIA'] == 'N/A' else ''} no-wrap" title="{sp['IFPMIA']}">{highlight_keywords(sp["IFPMIA"])}</td>
<td class="{'na' if sp['LS'] == 'N/A' else ''} no-wrap">{highlight_keywords(sp["LS"])}</td>
<td class="{'na' if sp['CYCLE'] == 'N/A' else ''} no-wrap">{highlight_keywords(sp["CYCLE"])}</td>
<td class="bypass-port-col no-wrap">{bypass_port}</td>
<td class="raw-value-col no-wrap" title="{setpoints_raw}">{highlight_keywords(setpoints_raw)}</td>
</tr>
"""
        idx += 1

html += """</tbody></table></div></div>

<div id="tab3" class="tab-content">
<h2>⚡ Voltage & Timing Settings</h2>
<div class="note">
<strong>Note:</strong> StartVoltages now parses QUAL patterns correctly
</div>
<div class="filter-controls">
<label><input type="checkbox" id="hideBypassPort1_tab3" onchange="toggleBypassPort('table3')"> Hide BypassPort = 1</label>
<label><input type="checkbox" id="hideBypassPortCol_tab3" onchange="toggleBypassPortCol('table3')"> Hide BypassPort Column</label>
<label><input type="checkbox" id="wrapText_tab3" onchange="toggleTextWrap('table3')"> Enable Text Wrapping</label>
<label>Font Size: 
<select id="fontSize_tab3" onchange="changeFontSize('table3', this.value)">
<option value="small">Small</option>
<option value="medium" selected>Medium</option>
<option value="large">Large</option>
</select>
</label>
</div>
<input type="text" class="search-box" id="search3" onkeyup="searchTable('search3', 'table3')" placeholder="Search...">
<div class="table-container">
<table id="table3">
<thead><tr>
<th><div class="resizer" data-table="table3"></div>#</th>
<th><div class="resizer" data-table="table3"></div>Instance Name</th>
<th><div class="resizer" data-table="table3"></div>Type</th>
<th><div class="resizer" data-table="table3"></div>Freq</th>
<th><div class="resizer" data-table="table3"></div>Corner</th>
<th><div class="resizer" data-table="table3"></div>VoltageTargets</th>
<th><div class="resizer" data-table="table3"></div>FivrCondition</th>
<th><div class="resizer" data-table="table3"></div>LevelsTc</th>
<th><div class="resizer" data-table="table3"></div>TimingsTc</th>
<th><div class="resizer" data-table="table3"></div>StartVoltages</th>
<th><div class="resizer" data-table="table3"></div>StepSize</th>
<th class="bypass-port-col"><div class="resizer" data-table="table3"></div>BypassPort</th>
</tr></thead>
<tbody>
"""

idx = 1
for group_name, group_instances in sorted_groups:
    html += f'<tr class="group-header"><td colspan="12">📁 {group_name}</td></tr>'

    for inst, cat in group_instances:
        voltage_targets = abbreviate_value(inst["parameters"].get("VoltageTargets", "N/A"), "VoltageTargets")
        fivr = remove_comments(inst["parameters"].get("FivrCondition", "N/A"))
        levels = abbreviate_value(inst["parameters"].get("LevelsTc", "N/A"), "LevelsTc")
        timings = abbreviate_value(inst["parameters"].get("TimingsTc", "N/A"), "TimingsTc")
        start_voltages = abbreviate_value(inst["parameters"].get("StartVoltages", "N/A"), "StartVoltages")
        step_size = abbreviate_value(inst["parameters"].get("StepSize", "N/A"), "StepSize")
        bypass_port = parse_die_value(inst["parameters"].get("BypassPort", "N/A"))

        html += f"""<tr data-bypass="{bypass_port}">
<td class="no-wrap">{idx}</td>
<td class="no-wrap" title="{inst['name']}"><strong>{highlight_keywords(inst["name"])}</strong></td>
<td class="{f'test-type-{cat["test_type"]}' if cat['test_type'] != 'N/A' else ''} no-wrap">{highlight_keywords(cat["test_type"])}</td>
<td class="no-wrap">{highlight_keywords(cat["frequency"])}</td>
<td class="no-wrap">{highlight_keywords(cat["instr_set"])}</td>
<td class="no-wrap" title="{voltage_targets}">{highlight_keywords(voltage_targets)}</td>
<td class="no-wrap">{highlight_keywords(fivr)}</td>
<td class="no-wrap" title="{levels}">{highlight_keywords(levels)}</td>
<td class="no-wrap" title="{timings}">{highlight_keywords(timings)}</td>
<td class="no-wrap">{highlight_keywords(start_voltages)}</td>
<td class="no-wrap">{highlight_keywords(step_size)}</td>
<td class="bypass-port-col no-wrap">{bypass_port}</td>
</tr>
"""
        idx += 1

html += """</tbody></table></div></div>

<div id="tab4" class="tab-content">
<h2>🎭 Mask & Pattern Configuration</h2>
<div class="filter-controls">
<label><input type="checkbox" id="hideBypassPort1_tab4" onchange="toggleBypassPort('table4')"> Hide BypassPort = 1</label>
<label><input type="checkbox" id="hideBypassPortCol_tab4" onchange="toggleBypassPortCol('table4')"> Hide BypassPort Column</label>
<label><input type="checkbox" id="wrapText_tab4" onchange="toggleTextWrap('table4')"> Enable Text Wrapping</label>
<label>Font Size: 
<select id="fontSize_tab4" onchange="changeFontSize('table4', this.value)">
<option value="small">Small</option>
<option value="medium" selected>Medium</option>
<option value="large">Large</option>
</select>
</label>
</div>
<input type="text" class="search-box" id="search4" onkeyup="searchTable('search4', 'table4')" placeholder="Search...">
<div class="table-container">
<table id="table4">
<thead><tr>
<th><div class="resizer" data-table="table4"></div>#</th>
<th><div class="resizer" data-table="table4"></div>Instance Name</th>
<th><div class="resizer" data-table="table4"></div>Type</th>
<th><div class="resizer" data-table="table4"></div>Freq</th>
<th><div class="resizer" data-table="table4"></div>Corner</th>
<th><div class="resizer" data-table="table4"></div>MaskBuilderSettings</th>
<th><div class="resizer" data-table="table4"></div>DecoderConfiguration</th>
<th><div class="resizer" data-table="table4"></div>MultiPassMasks</th>
<th><div class="resizer" data-table="table4"></div>PreInstance</th>
<th class="bypass-port-col"><div class="resizer" data-table="table4"></div>BypassPort</th>
</tr></thead>
<tbody>
"""

idx = 1
for group_name, group_instances in sorted_groups:
    html += f'<tr class="group-header"><td colspan="10">📁 {group_name}</td></tr>'

    for inst, cat in group_instances:
        mask_builder = abbreviate_value(inst["parameters"].get("MaskBuilderSettings", "N/A"), "MaskBuilderSettings")
        decoder = abbreviate_value(inst["parameters"].get("DecoderConfiguration", "N/A"), "DecoderConfiguration")
        multi_pass = remove_comments(abbreviate_value(inst["parameters"].get("MultiPassMasks", "N/A"), "MultiPassMasks"))
        pre_instance = remove_comments(inst["parameters"].get("PreInstance", "N/A"))
        bypass_port = parse_die_value(inst["parameters"].get("BypassPort", "N/A"))

        html += f"""<tr data-bypass="{bypass_port}">
<td class="no-wrap">{idx}</td>
<td class="no-wrap" title="{inst['name']}"><strong>{highlight_keywords(inst["name"])}</strong></td>
<td class="{f'test-type-{cat["test_type"]}' if cat['test_type'] != 'N/A' else ''} no-wrap">{highlight_keywords(cat["test_type"])}</td>
<td class="no-wrap">{highlight_keywords(cat["frequency"])}</td>
<td class="no-wrap">{highlight_keywords(cat["instr_set"])}</td>
<td class="no-wrap" title="{mask_builder}">{highlight_keywords(mask_builder)}</td>
<td class="no-wrap" title="{decoder}">{highlight_keywords(decoder)}</td>
<td class="no-wrap" title="{multi_pass}">{highlight_keywords(multi_pass)}</td>
<td class="no-wrap" title="{pre_instance}">{highlight_keywords(pre_instance)}</td>
<td class="bypass-port-col no-wrap">{bypass_port}</td>
</tr>
"""
        idx += 1

html += """</tbody></table></div></div>

<div id="tab5" class="tab-content">
<h2>📖 Abbreviations Reference</h2>
<div class="note">
<strong>Note:</strong> Mapping between abbreviated values (shown in report) and original full values from MTPL file.
</div>
<div class="abbrev-table">
<h3>Value Abbreviations</h3>
<table>
<thead>
<tr>
<th style="width: 40%;">Abbreviated Value</th>
<th style="width: 60%;">Original Value</th>
</tr>
</thead>
<tbody>
"""

for abbrev, original in sorted(abbreviation_map.items()):
    html += f"""<tr>
<td><strong>{abbrev}</strong></td>
<td style="font-size: 0.9em;">{original}</td>
</tr>
"""

html += """</tbody>
</table>
</div>
</div>

</div>

<script>
// Column resizing functionality
document.addEventListener('DOMContentLoaded', function() {
  const resizers = document.querySelectorAll('.resizer');
  let currentResizer, currentTh, startX, startWidth;
  
  resizers.forEach(function(resizer) {
    resizer.addEventListener('mousedown', function(e) {
      currentResizer = e.target;
      currentTh = currentResizer.parentElement;
      startX = e.pageX;
      startWidth = currentTh.offsetWidth;
      
      document.addEventListener('mousemove', resize);
      document.addEventListener('mouseup', stopResize);
      e.preventDefault();
    });
  });
  
  function resize(e) {
    if (currentTh) {
      const width = startWidth + (e.pageX - startX);
      currentTh.style.width = width + 'px';
      currentTh.style.minWidth = width + 'px';
    }
  }
  
  function stopResize() {
    document.removeEventListener('mousemove', resize);
    document.removeEventListener('mouseup', stopResize);
    currentResizer = null;
    currentTh = null;
  }
});

function openTab(evt, tabName) {
  var tabcontent = document.getElementsByClassName("tab-content");
  for (var i = 0; i < tabcontent.length; i++) {
    tabcontent[i].classList.remove("active");
  }
  var tablinks = document.getElementsByClassName("tab-button");
  for (var i = 0; i < tablinks.length; i++) {
    tablinks[i].classList.remove("active");
  }
  document.getElementById(tabName).classList.add("active");
  evt.currentTarget.classList.add("active");
}

function toggleBypassPort(tableId) {
  var table = document.getElementById(tableId);
  var checkboxId = "hideBypassPort1_" + tableId.replace("table", "tab");
  var checkbox = document.getElementById(checkboxId);
  var rows = table.getElementsByTagName("tr");

  // First pass: hide/show rows based on BypassPort value
  var visibleRowsPerGroup = {};
  var currentGroup = null;

  for (var i = 0; i < rows.length; i++) {
    if (rows[i].classList.contains("group-header")) {
      currentGroup = i;
      visibleRowsPerGroup[currentGroup] = 0;
      continue;
    }

    var bypassPort = rows[i].getAttribute("data-bypass");
    if (checkbox.checked && bypassPort === "1") {
      rows[i].classList.add("hidden-row");
    } else {
      rows[i].classList.remove("hidden-row");
    }

    // Count visible rows (not hidden by BypassPort and not hidden by search)
    if (!rows[i].classList.contains("hidden-row") && rows[i].style.display !== "none") {
      if (currentGroup !== null) {
        visibleRowsPerGroup[currentGroup]++;
      }
    }
  }

  // Second pass: hide group headers with no visible children
  for (var groupIdx in visibleRowsPerGroup) {
    var groupRow = rows[groupIdx];
    if (checkbox.checked && visibleRowsPerGroup[groupIdx] === 0) {
      groupRow.style.display = "none";
    } else {
      groupRow.style.display = "";
    }
  }
}

function toggleBypassPortCol(tableId) {
  var checkboxId = "hideBypassPortCol_" + tableId.replace("table", "tab");
  var checkbox = document.getElementById(checkboxId);
  var cols = document.querySelectorAll("#" + tableId + " .bypass-port-col");
  
  for (var i = 0; i < cols.length; i++) {
    if (checkbox.checked) {
      cols[i].classList.add("hidden-col");
    } else {
      cols[i].classList.remove("hidden-col");
    }
  }
}

function toggleRawValue() {
  var checkbox = document.getElementById("hideRawValue_tab2");
  var cols = document.querySelectorAll(".raw-value-col");
  
  for (var i = 0; i < cols.length; i++) {
    if (checkbox.checked) {
      cols[i].classList.add("hidden-col");
    } else {
      cols[i].classList.remove("hidden-col");
    }
  }
}

function toggleTextWrap(tableId) {
  var checkboxId = "wrapText_" + tableId.replace("table", "tab");
  var checkbox = document.getElementById(checkboxId);
  var table = document.getElementById(tableId);
  var cells = table.getElementsByTagName("td");
  
  for (var i = 0; i < cells.length; i++) {
    if (checkbox.checked) {
      cells[i].classList.remove("no-wrap");
      cells[i].classList.add("wrap-text");
    } else {
      cells[i].classList.remove("wrap-text");
      cells[i].classList.add("no-wrap");
    }
  }
}

function changeFontSize(tableId, size) {
  var table = document.getElementById(tableId);
  var tbody = table.getElementsByTagName("tbody")[0];
  
  tbody.classList.remove("font-small", "font-medium", "font-large");
  
  if (size === "small") {
    tbody.classList.add("font-small");
  } else if (size === "large") {
    tbody.classList.add("font-large");
  } else {
    tbody.classList.add("font-medium");
  }
}

function searchTable(inputId, tableId) {
  var input = document.getElementById(inputId);
  var filter = input.value.toUpperCase();
  var table = document.getElementById(tableId);
  var tr = table.getElementsByTagName("tr");

  // First pass: mark rows as visible/hidden based on search
  var visibleRowsPerGroup = {};
  var currentGroup = null;

  for (var i = 1; i < tr.length; i++) {
    if (tr[i].classList.contains("group-header")) {
      currentGroup = i;
      visibleRowsPerGroup[currentGroup] = 0;

      // Check if group header itself matches the filter
      var groupText = tr[i].textContent || tr[i].innerText;
      if (filter === "" || groupText.toUpperCase().indexOf(filter) > -1) {
        tr[i].setAttribute("data-group-match", "true");
      } else {
        tr[i].setAttribute("data-group-match", "false");
      }
      continue;
    }

    // Skip rows already hidden by BypassPort filter
    if (tr[i].classList.contains("hidden-row")) {
      tr[i].style.display = "none";
      continue;
    }

    var found = false;
    var td = tr[i].getElementsByTagName("td");
    for (var j = 0; j < td.length; j++) {
      if (td[j] && !td[j].classList.contains("hidden-col")) {
        var txtValue = td[j].textContent || td[j].innerText;
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
          found = true;
          break;
        }
      }
    }

    tr[i].style.display = found ? "" : "none";
    if (found && currentGroup !== null) {
      visibleRowsPerGroup[currentGroup]++;
    }
  }

  // Second pass: hide group headers with no visible children
  for (var groupIdx in visibleRowsPerGroup) {
    var groupRow = tr[groupIdx];
    var groupMatch = groupRow.getAttribute("data-group-match") === "true";
    var hasVisibleChildren = visibleRowsPerGroup[groupIdx] > 0;

    if (filter === "") {
      groupRow.style.display = "";
    } else if (groupMatch || hasVisibleChildren) {
      groupRow.style.display = "";
    } else {
      groupRow.style.display = "none";
    }
  }
}
</script>
</body>
</html>"""

with open(output_file, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ Report generated: {output_file}")
print(f"📊 SBFT Instances: {len(sbft_instances)}")
print(f"📁 Grouped into: {len(grouped)} categories")
print(f"📖 Abbreviations tracked: {len(abbreviation_map)}")
print(f"\n✅ NEW FEATURES:")
print(f"   ✓ SIGOFF: Green Bold Italic formatting")
print(f"   ✓ SIGON: Blue Bold formatting")
print(f"   ✓ StartVoltages: QUAL parsing with UCCX1/UCCX4 logic")
print(f"   ✓ Comment removal: All # comments stripped")
print(f"   ✓ Hide BypassPort Column: Checkbox on all tabs")
print(f"   ✓ Sticky headers: Headers stay visible when scrolling")
