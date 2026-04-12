#!/usr/bin/env python3
"""Generate the skill selection benchmark dataset.

Usage:
    python datasets/skill_selection/generate.py

Output:
    datasets/skill_selection/skill_selection_dataset.csv

Upload to Kaggle:
    kaggle datasets version -p datasets/skill_selection/ -m "Regenerated"
"""

import json
import os
import random
import sys

import pandas as pd

# === Nexara Platform: synthetic tool registry ===

PREFIXES = ['flux', 'glyph', 'prism', 'vex', 'quill', 'rune', 'arc', 'shard',
            'drift', 'nexus', 'pulse', 'cipher', 'loom', 'anvil', 'haze',
            'bolt', 'thorn', 'crest', 'orbit', 'ember']

SUFFIXES = ['bridge', 'weaver', 'forge', 'scanner', 'render', 'mapper', 'linker',
            'splitter', 'parser', 'binder', 'tracer', 'solver', 'router', 'sealer',
            'minter', 'crafter', 'sifter', 'blender', 'fuser', 'stacker']

DOMAINS = [
    'signal_routing', 'pattern_synthesis', 'schema_validation',
    'index_compaction', 'token_expansion', 'stream_alignment',
    'cache_projection', 'graph_traversal', 'format_conversion',
    'anomaly_isolation', 'queue_balancing', 'ledger_reconcile',
    'mesh_optimization', 'sequence_generation', 'state_snapshot'
]

DOMAIN_DESCRIPTIONS = {
    'signal_routing': 'Routes incoming signals to designated endpoints based on protocol headers and priority flags.',
    'pattern_synthesis': 'Synthesizes recurring motifs from raw data streams to build composite templates.',
    'schema_validation': 'Validates incoming payloads against registered schema definitions and constraint sets.',
    'index_compaction': 'Compresses and defragments index structures to reclaim storage and speed up lookups.',
    'token_expansion': 'Expands compressed token sequences into their full representations for downstream processing.',
    'stream_alignment': 'Aligns parallel data streams by timestamp or sequence markers to enable synchronized reads.',
    'cache_projection': 'Projects frequently accessed data subsets into fast-access cache layers for low-latency retrieval.',
    'graph_traversal': 'Navigates node-edge structures to discover paths, cycles, and connected components.',
    'format_conversion': 'Transforms data between serialization formats such as binary, columnar, and tagged encodings.',
    'anomaly_isolation': 'Detects and quarantines outlier records that deviate from established statistical baselines.',
    'queue_balancing': 'Redistributes message backlog across consumer partitions to equalize processing load.',
    'ledger_reconcile': 'Cross-references transaction entries across ledger replicas to surface discrepancies.',
    'mesh_optimization': 'Re-weights edges in service mesh topologies to minimize latency and maximize throughput.',
    'sequence_generation': 'Produces ordered identifier sequences with configurable prefixes, checksums, and gaps.',
    'state_snapshot': 'Captures point-in-time snapshots of system state for rollback, audit, and diff analysis.'
}

DOMAIN_CAPABILITIES = {
    'signal_routing': ['route signals by protocol', 'apply priority-based dispatch', 'handle endpoint failover'],
    'pattern_synthesis': ['extract recurring motifs', 'build composite templates', 'merge partial patterns'],
    'schema_validation': ['validate payload structure', 'check constraint compliance', 'report schema violations'],
    'index_compaction': ['defragment index pages', 'reclaim storage blocks', 'rebuild sorted pointers'],
    'token_expansion': ['decode compressed tokens', 'expand abbreviation sequences', 'restore full representations'],
    'stream_alignment': ['synchronize parallel streams', 'align by timestamp markers', 'merge ordered channels'],
    'cache_projection': ['project hot subsets to cache', 'manage eviction policies', 'track access frequency'],
    'graph_traversal': ['traverse node-edge graphs', 'detect cycles and paths', 'compute connected components'],
    'format_conversion': ['transform serialization formats', 'convert binary to columnar', 'remap tagged encodings'],
    'anomaly_isolation': ['detect statistical outliers', 'quarantine anomalous records', 'score deviation magnitude'],
    'queue_balancing': ['redistribute message backlog', 'equalize consumer load', 'rebalance partitions dynamically'],
    'ledger_reconcile': ['cross-reference ledger entries', 'surface transaction discrepancies', 'reconcile replica drift'],
    'mesh_optimization': ['reweight mesh edges', 'minimize service latency', 'optimize throughput topology'],
    'sequence_generation': ['produce ordered identifiers', 'apply checksum prefixes', 'configure sequence gaps'],
    'state_snapshot': ['capture point-in-time state', 'enable rollback operations', 'generate diff reports']
}

CONFUSABLE_DESCRIPTIONS = {
    'signal_routing': 'Processes incoming data flows and manages their distribution across system components.',
    'pattern_synthesis': 'Processes data streams to identify structures and organize them into usable outputs.',
    'schema_validation': 'Inspects incoming data for structural compliance and flags potential issues.',
    'index_compaction': 'Optimizes internal data structures for improved system performance and resource usage.',
    'token_expansion': 'Processes compressed data elements and prepares them for further system operations.',
    'stream_alignment': 'Coordinates multiple data channels to ensure consistent processing order.',
    'cache_projection': 'Manages data placement strategies to optimize access patterns and reduce latency.',
    'graph_traversal': 'Explores interconnected data structures to extract relationship information.',
    'format_conversion': 'Handles data transformation between different internal representation standards.',
    'anomaly_isolation': 'Monitors data quality metrics and manages records that fall outside normal parameters.',
    'queue_balancing': 'Manages workload distribution to maintain consistent processing throughput.',
    'ledger_reconcile': 'Compares data records across storage locations to ensure consistency.',
    'mesh_optimization': 'Adjusts system interconnection parameters to improve overall performance.',
    'sequence_generation': 'Produces structured identifiers and manages ordering within the data pipeline.',
    'state_snapshot': 'Creates data checkpoints for system recovery and change tracking purposes.'
}

ADVERSARIAL_DESC_MAP = {
    'signal_routing': ('Synthesizes composite data templates from fragmented input sources.', 'pattern_synthesis'),
    'pattern_synthesis': ('Validates structural compliance of incoming payloads against reference models.', 'schema_validation'),
    'schema_validation': ('Navigates hierarchical data structures to discover hidden linkages.', 'graph_traversal'),
    'index_compaction': ('Redistributes processing tasks across available worker nodes for balanced throughput.', 'queue_balancing'),
    'token_expansion': ('Captures system state at regular intervals for recovery and auditing.', 'state_snapshot'),
    'stream_alignment': ('Detects deviations from expected data patterns and flags suspicious entries.', 'anomaly_isolation'),
    'cache_projection': ('Transforms data between storage formats for cross-platform compatibility.', 'format_conversion'),
    'graph_traversal': ('Compresses and reorganizes lookup indices to accelerate query performance.', 'index_compaction'),
    'format_conversion': ('Routes incoming requests to appropriate handlers based on content classification.', 'signal_routing'),
    'anomaly_isolation': ('Aligns timestamps across distributed event logs for unified analysis.', 'stream_alignment'),
    'queue_balancing': ('Projects hot data segments into accelerated storage tiers.', 'cache_projection'),
    'ledger_reconcile': ('Generates unique sequential codes with embedded verification checksums.', 'sequence_generation'),
    'mesh_optimization': ('Expands abbreviated token streams into their full decoded forms.', 'token_expansion'),
    'sequence_generation': ('Cross-checks distributed records to identify and resolve inconsistencies.', 'ledger_reconcile'),
    'state_snapshot': ('Reweights network pathways to reduce end-to-end communication delays.', 'mesh_optimization')
}

TASK_TEMPLATES = {
    'signal_routing': [
        'We need to direct incoming API calls to the correct backend service based on their header metadata.',
        'Our system receives mixed-priority messages and must dispatch each one to the right handler.',
        'Find me a tool that can take inbound packets and forward them to the appropriate processing endpoint.',
    ],
    'pattern_synthesis': [
        'We have fragmented log entries that share common structures — we need to merge them into unified templates.',
        'I need to combine partial observations from multiple sensors into a single coherent representation.',
        'Help me consolidate repeated structural motifs from our telemetry data into reusable blueprints.',
    ],
    'schema_validation': [
        'Before ingesting user submissions, we need to verify they conform to our expected data format.',
        'Our pipeline occasionally receives malformed records — I need automated structural checks.',
        'I need to ensure every incoming JSON object meets our defined field requirements.',
    ],
    'index_compaction': [
        'Our lookup tables have become fragmented after months of inserts and deletes — they need consolidation.',
        'Query performance has degraded because our search indices have accumulated dead entries.',
        'We need to reclaim wasted storage in our key-value store by reorganizing the internal page layout.',
    ],
    'token_expansion': [
        'Our upstream system sends abbreviated codes that need to be decoded into their full form before analysis.',
        'I have a stream of shorthand notation that must be unpacked into verbose representations.',
        'The data arrives in a compressed symbolic format — expand each symbol to its complete meaning.',
    ],
    'stream_alignment': [
        'Two independent event feeds must be merged in chronological order despite different clock sources.',
        'Our left and right sensor arrays produce data at different rates — synchronize them by timestamp.',
        'I need to combine readings from distributed nodes so they appear as a single time-ordered sequence.',
    ],
    'cache_projection': [
        'Our most-requested datasets should be preloaded into a faster storage tier to cut response times.',
        'I need to keep a working set of hot records close to the compute layer for instant access.',
        'Set up a mechanism to mirror frequently hit data segments into a low-latency memory region.',
    ],
    'graph_traversal': [
        'We have a network of dependencies between modules — find all reachable components from a given root.',
        'Given a set of linked entities, determine if any circular references exist among them.',
        'I need to walk through a hierarchy of connected nodes and list every path to the leaf level.',
    ],
    'format_conversion': [
        'Our partner sends data in a columnar binary layout, but our system expects tagged text records.',
        'Convert the archived files from their legacy encoding into our current standard representation.',
        'I need to translate between two different serialization schemes without losing field semantics.',
    ],
    'anomaly_isolation': [
        'Some of our sensor readings look like extreme outliers — identify and separate them for review.',
        'Flag any transaction amounts that fall well outside the historical norm for that account type.',
        'We suspect a few corrupted entries in the dataset — find records that deviate significantly from peers.',
    ],
    'queue_balancing': [
        'Some of our worker nodes are overwhelmed while others sit idle — rebalance the pending jobs.',
        'Our message consumers have uneven backlogs — redistribute tasks to equalize processing time.',
        'The job queue has become skewed toward a few partitions — spread the load evenly.',
    ],
    'ledger_reconcile': [
        'Two copies of our financial log have drifted apart — we need to find where they disagree.',
        'Compare the master and replica transaction records and list every mismatch.',
        'After a sync failure, verify that both sides of the double-entry system still agree.',
    ],
    'mesh_optimization': [
        'Our microservices communicate over a mesh network — tune the link weights to reduce round-trip time.',
        'The inter-service communication graph has suboptimal routing — adjust it for maximum bandwidth.',
        'I need to reconfigure the network topology between services to minimize end-to-end delay.',
    ],
    'sequence_generation': [
        'We need to mint a batch of unique order numbers with embedded check digits.',
        'Generate a series of tracking codes that follow our prefix-counter-checksum convention.',
        'Produce a set of consecutively numbered identifiers, each with a built-in verification suffix.',
    ],
    'state_snapshot': [
        'Before applying the migration, freeze the current system state so we can roll back if needed.',
        'Capture a full image of the running configuration for our nightly audit comparison.',
        'I need a before-and-after picture of the database contents to generate a change report.',
    ],
}

# === Generation functions ===

NUM_TOOLS = [5, 15, 30]
SIMILARITIES = ['distinct', 'confusable', 'adversarial']
SIMILARITY_SEED = {'distinct': 0, 'confusable': 1, 'adversarial': 2}  # deterministic, no hash()
SEEDS = 3
STUDY_EXAMPLE_COUNTS = {5: 4, 15: 6, 30: 8}


def generate_tool_name(rng, used_names):
    for _ in range(200):
        name = f'{rng.choice(PREFIXES)}_{rng.choice(SUFFIXES)}'
        if name not in used_names:
            used_names.add(name)
            return name
    raise ValueError('Could not generate unique tool name')


def generate_registry(rng, num_tools, similarity):
    used_names = set()
    tools = []
    domains_pool = list(DOMAINS)
    rng.shuffle(domains_pool)
    selected_domains = []
    while len(selected_domains) < num_tools:
        selected_domains.extend(domains_pool)
    selected_domains = selected_domains[:num_tools]
    selected_domains = list(dict.fromkeys(selected_domains))[:num_tools]
    if len(selected_domains) < num_tools:
        remaining = [d for d in DOMAINS if d not in selected_domains]
        rng.shuffle(remaining)
        selected_domains.extend(remaining[:num_tools - len(selected_domains)])

    domain_to_tool = {}
    for domain in selected_domains:
        name = generate_tool_name(rng, used_names)
        if similarity == 'distinct':
            desc = DOMAIN_DESCRIPTIONS[domain]
        elif similarity == 'confusable':
            desc = CONFUSABLE_DESCRIPTIONS[domain]
        else:
            desc = ADVERSARIAL_DESC_MAP[domain][0]
        caps = DOMAIN_CAPABILITIES[domain]
        tools.append({'name': name, 'domain': domain, 'description': desc, 'capabilities': caps})
        domain_to_tool[domain] = name

    rng.shuffle(tools)
    return tools, domain_to_tool


def format_registry(tools):
    lines = ['=== Nexara Platform — Tool Registry ===', '']
    for i, t in enumerate(tools, 1):
        lines.append(f'{i}. **{t["name"]}**')
        lines.append(f'   Description: {t["description"]}')
        lines.append(f'   Capabilities:')
        for cap in t['capabilities']:
            lines.append(f'     - {cap}')
        lines.append('')
    return '\n'.join(lines)


def generate_study_examples(rng, tools, domain_to_tool, num_examples, similarity, exclude_domain):
    examples = []
    available_domains = [t['domain'] for t in tools if t['domain'] != exclude_domain]
    rng.shuffle(available_domains)
    domains_for_examples = available_domains[:num_examples]
    if len(domains_for_examples) < num_examples:
        domains_for_examples.extend([exclude_domain] * (num_examples - len(domains_for_examples)))

    for domain in domains_for_examples[:num_examples]:
        task = rng.choice(TASK_TEMPLATES[domain])
        correct_tool = domain_to_tool[domain]
        tool_entry = next(t for t in tools if t['name'] == correct_tool)
        if similarity == 'adversarial':
            explanation = (f'Despite its name and description suggesting a different purpose, '
                          f'{correct_tool} is the correct choice because its CAPABILITIES list '
                          f'({", ".join(tool_entry["capabilities"][:2])}) directly match this task. '
                          f'Always look at capabilities, not names or descriptions.')
        else:
            explanation = (f'{correct_tool} is correct because its capabilities '
                          f'({", ".join(tool_entry["capabilities"][:2])}) '
                          f'directly address what this task requires.')
        examples.append({'task': task, 'correct_tool': correct_tool, 'explanation': explanation})
    return examples


def format_study_examples(examples):
    lines = ['Here are practice examples of selecting the correct tool:', '']
    for i, ex in enumerate(examples, 1):
        lines.append(f'Example {i}:')
        lines.append(f'  Task: {ex["task"]}')
        lines.append(f'  Correct tool: {ex["correct_tool"]}')
        lines.append(f'  Why: {ex["explanation"]}')
        lines.append('')
    return '\n'.join(lines)


def generate_dataset():
    rows = []
    tid = 0
    for num_tools in NUM_TOOLS:
        for similarity in SIMILARITIES:
            for seed in range(SEEDS):
                rng = random.Random(seed * 100 + num_tools * 10 + SIMILARITY_SEED[similarity])
                tools, domain_to_tool = generate_registry(rng, num_tools, similarity)

                target_domain = list(domain_to_tool.keys())[seed % len(domain_to_tool)]
                target_tool = domain_to_tool[target_domain]
                task_templates = TASK_TEMPLATES[target_domain]
                test_input = task_templates[seed % len(task_templates)]

                material = format_registry(tools)
                valid_names = json.dumps([t['name'] for t in tools])

                n_study = STUDY_EXAMPLE_COUNTS[num_tools]
                study_examples = generate_study_examples(
                    rng, tools, domain_to_tool, n_study, similarity, target_domain)
                study_material = format_study_examples(study_examples)

                difficulty_label = f'{num_tools}tools_{similarity}'
                rows.append({
                    'task_id': tid, 'seed': seed, 'num_tools': num_tools,
                    'similarity': similarity, 'difficulty_label': difficulty_label,
                    'material': material, 'study_material': study_material,
                    'test_input': test_input, 'expected': target_tool,
                    'item_desc': f'{num_tools}tools_{similarity}_s{seed}',
                    'test_domain': target_domain, 'valid_names': valid_names,
                })
                tid += 1

    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'skill_selection_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'expected', 'test_domain']].to_string(index=False))
