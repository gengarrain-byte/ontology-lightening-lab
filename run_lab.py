"""Independent, deterministic RDF study lab. No remote endpoints or model calls."""
import argparse
import csv
import gzip
import html
import importlib.metadata
import json
import platform
import statistics
import time
from pathlib import Path

from owlrl import DeductiveClosure, RDFS_Semantics
from pyshacl import validate
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import DCTERMS, RDF, RDFS, SH, XSD
from rdflib.plugins.sparql import prepareQuery

ROOT = Path(__file__).resolve().parent
EX = Namespace('https://example.org/learning/')
QUERIES = {
    'Q1_topic_0': 'SELECT DISTINCT ?r WHERE { ?r ex:coversTopic ex:topic_0 }',
    'Q2_resources': 'SELECT DISTINCT ?r WHERE { ?r a ex:LearningResource }',
    'Q3_missing_author': '''SELECT DISTINCT ?r WHERE {
      ?r a ex:LearningResource . FILTER NOT EXISTS { ?r ex:authoredBy ?a }
    }''',
    'Q4_provenance': '''SELECT DISTINCT ?r ?s ?row WHERE {
      ?r ex:sourceRecord ?s . ?s ex:row ?row
    }''',
    'Q5_text_resources': 'SELECT DISTINCT ?r WHERE { ?r a ex:TextResource }',
}


def graph_copy(g):
    out = Graph()
    for prefix, uri in g.namespaces():
        out.bind(prefix, uri)
    out += g
    return out


def closure(g):
    out = graph_copy(g)
    start = time.perf_counter()
    DeductiveClosure(RDFS_Semantics, axiomatic_triples=False,
                     datatype_axioms=False).expand(out)
    return out, (time.perf_counter() - start) * 1000


def result_set(g, prepared):
    return {tuple(term.n3() if term is not None else None for term in row)
            for row in g.query(prepared)}


def shacl_result(g, shapes):
    conforms, report, _ = validate(g, shacl_graph=shapes,
                                  inference='none', inplace=False)
    issues = sorted((str(report.value(r, SH.focusNode)),
                     str(report.value(r, SH.resultPath)),
                     str(report.value(r, SH.sourceConstraintComponent)))
                    for r in report.subjects(RDF.type, SH.ValidationResult))
    return {'conforms': bool(conforms), 'violations': issues}


def run(n, repeats):
    out = ROOT / f'run-{n}'
    out.mkdir(exist_ok=True)
    ontology = Graph().parse(ROOT / 'ontology.ttl', format='turtle')
    shapes = Graph().parse(ROOT / 'shapes.ttl', format='turtle')
    csv_path = out / 'source.csv'
    unique_rows = []
    for i in range(n):
        unique_rows.append({
            'id': f'resource_{i:05d}',
            'kind': 'Article' if i % 2 == 0 else 'Course',
            'title': 'Same title, distinct resources' if i < 2 else f'Learning material {i}',
            'author': '' if i % 97 == 7 else f'person_{i % 20:02d}',
            'topic': f'topic_{i % 6}',
        })
    physical_rows = []
    for i, row in enumerate(unique_rows):
        physical_rows.append(row)
        if i % 17 == 0:
            physical_rows.append(row.copy())
    with csv_path.open('w', newline='', encoding='utf8') as f:
        w = csv.DictWriter(f, fieldnames=list(unique_rows[0]))
        w.writeheader()
        w.writerows(physical_rows)

    # Stable source IDs identify the logical record; first physical CSV row is its locator.
    g = graph_copy(ontology)
    g.bind('ex', EX)
    g.bind('dct', DCTERMS)
    seen = set()
    with csv_path.open(encoding='utf8', newline='') as f:
        for line, row in enumerate(csv.DictReader(f), start=2):
            if row['id'] in seen:
                continue
            seen.add(row['id'])
            r, src = EX[row['id']], EX['source_' + row['id']]
            g.add((r, RDF.type, EX[row['kind']]))
            g.add((r, DCTERMS.title, Literal(row['title'])))
            g.add((r, EX.coversTopic, EX[row['topic']]))
            g.add((r, EX.sourceRecord, src))
            g.add((src, EX.row, Literal(line, datatype=XSD.integer)))
            if row['author']:
                g.add((r, EX.authoredBy, EX[row['author']]))
                g.add((EX[row['author']], DCTERMS.title, Literal(row['author'])))
    for i in range(6):
        g.add((EX[f'topic_{i}'], DCTERMS.title, Literal(f'Topic {i}')))

    storage = []
    for fmt, name in [('nt', 'graph.nt'), ('turtle', 'graph.ttl'), ('xml', 'graph.rdf')]:
        data = g.serialize(format=fmt, encoding='utf8')
        (out / name).write_bytes(data)
        restored = Graph().parse(data=data, format=fmt)
        equal = set(restored) == set(g)  # This graph contains no blank nodes.
        assert equal, f'Round trip mismatch for {fmt}'
        storage.append({'format': fmt, 'file': name, 'bytes': len(data), 'graph_equal': equal})
    turtle = (out / 'graph.ttl').read_bytes()
    compressed = gzip.compress(turtle, compresslevel=9, mtime=0)
    (out / 'graph.ttl.gz').write_bytes(compressed)
    restored_bytes = gzip.decompress(compressed)
    restored = Graph().parse(data=restored_bytes, format='turtle')
    assert restored_bytes == turtle and set(restored) == set(g)
    storage.append({'format': 'turtle+gzip', 'file': 'graph.ttl.gz',
                    'bytes': len(compressed), 'graph_equal': True})

    full, closure_ms = closure(g)
    restored_full, _ = closure(restored)
    selected = set(g.subjects(EX.coversTopic, EX.topic_0))
    partial = graph_copy(ontology)
    support = set(selected)
    for r in selected:
        support.update(o for _, _, o in g.triples((r, None, None)) if not isinstance(o, Literal))
    for subject in support:
        for triple in g.triples((subject, None, None)):
            partial.add(triple)
    partial_full, partial_closure_ms = closure(partial)
    partial.serialize(out / 'topic-0.ttl', format='turtle')

    # Materialise only the types needed by this registered query workload.
    selective = graph_copy(g)
    for cls in [EX.LearningResource, EX.TextResource]:
        for r in full.subjects(RDF.type, cls):
            selective.add((r, RDF.type, cls))
    selective.serialize(out / 'selective-types.ttl', format='turtle')

    no_provenance = graph_copy(g)
    for t in list(no_provenance.triples((None, EX.sourceRecord, None))):
        no_provenance.remove(t)
    no_provenance_full, _ = closure(no_provenance)
    broken_schema = graph_copy(g)
    broken_schema.remove((EX.Article, RDFS.subClassOf, EX.TextResource))
    broken_full, _ = closure(broken_schema)

    variants = {'full_rdfs': full, 'gzip_restored_rdfs': restored_full,
                'topic_0_rdfs': partial_full, 'selective_types': selective,
                'removed_provenance_rdfs': no_provenance_full,
                'broken_hierarchy_rdfs': broken_full}
    prepared = {key: prepareQuery(value, initNs={'ex': EX}) for key, value in QUERIES.items()}
    for key, query in QUERIES.items():
        (out / f'{key}.rq').write_text('PREFIX ex: <https://example.org/learning/>\n' + query, encoding='utf8')
    answers = {variant: {q: result_set(vg, pq) for q, pq in prepared.items()}
               for variant, vg in variants.items()}
    baseline = answers['full_rdfs']
    checks = []
    for variant in variants:
        for q in QUERIES:
            reference, candidate = baseline[q], answers[variant][q]
            checks.append({'variant': variant, 'query': q, 'count': len(candidate),
                           'same_global_answers': reference == candidate,
                           'missing': len(reference - candidate), 'extra': len(candidate - reference)})
    assert all(answers['gzip_restored_rdfs'][q] == baseline[q] for q in QUERIES)
    assert all(answers['selective_types'][q] == baseline[q] for q in QUERIES)
    assert answers['topic_0_rdfs']['Q1_topic_0'] == baseline['Q1_topic_0']
    assert answers['topic_0_rdfs']['Q2_resources'] != baseline['Q2_resources']
    assert answers['removed_provenance_rdfs']['Q1_topic_0'] == baseline['Q1_topic_0']
    assert not answers['removed_provenance_rdfs']['Q4_provenance']
    assert baseline['Q5_text_resources'] and not answers['broken_hierarchy_rdfs']['Q5_text_resources']
    scope_checks = []
    selected_n3 = {r.n3() for r in selected}
    for q in QUERIES:
        scoped_reference = {row for row in baseline[q] if row[0] in selected_n3}
        assert scoped_reference == answers['topic_0_rdfs'][q]
        scope_checks.append({'query': q, 'selected_scope_equal': True, 'count': len(scoped_reference)})

    shacl = {name: shacl_result(variants[name], shapes)
             for name in ['full_rdfs', 'gzip_restored_rdfs', 'selective_types', 'topic_0_rdfs']}
    assert shacl['full_rdfs'] == shacl['gzip_restored_rdfs'] == shacl['selective_types']
    assert not shacl['full_rdfs']['conforms']
    timings = {name: {q: [] for q in QUERIES} for name in ['full_rdfs', 'topic_0_rdfs', 'selective_types']}
    # All queries have already run once. These are warm, in-process, full-result timings.
    for _ in range(repeats):
        for name in timings:
            for q, pq in prepared.items():
                start = time.perf_counter()
                result_set(variants[name], pq)
                timings[name][q].append((time.perf_counter() - start) * 1000)
    report = {
        'records': n, 'physical_csv_rows': len(physical_rows), 'duplicate_rows': len(physical_rows) - n,
        'schema_triples': len(ontology), 'explicit_triples_with_schema': len(g),
        'rdfs_triples': len(full), 'selected_records': len(selected),
        'partial_explicit_triples': len(partial), 'partial_rdfs_triples': len(partial_full),
        'selective_type_triples': len(selective), 'storage': storage,
        'closure_ms': {'full': closure_ms, 'partial': partial_closure_ms},
        'answer_checks': checks, 'scope_checks': scope_checks, 'shacl': shacl,
        'warm_query_ms': timings, 'repeats': repeats,
        'environment': {'python': platform.python_version(), 'system': platform.system(),
                        'architecture': platform.machine(),
                        'packages': {p: importlib.metadata.version(p) for p in ['rdflib', 'owlrl', 'pyshacl']}},
        'limits': ['Synthetic structured data; not a production or million-document benchmark.',
                   'In-memory RDFLib store; file bytes are not database or heap measurements.',
                   'RDFS closure, not full OWL DL or an EL/QL/RL profile conversion.',
                   'Subset extraction is explicit ABox scope selection, not a formal TBox module extractor.',
                   'Selective type materialisation preserves only the registered workload tested here.',
                   'Warm timings include full result enumeration; exclude loading, query preparation and closure.',
                   'gzip must be decompressed before RDFLib parsing; no direct compressed query claim.'],
    }
    (out / 'results.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf8')
    write_pages(out, report)
    print(json.dumps({k: report[k] for k in ['records', 'physical_csv_rows', 'explicit_triples_with_schema',
                                           'rdfs_triples', 'selected_records', 'partial_explicit_triples',
                                           'selective_type_triples', 'storage']}, ensure_ascii=False), flush=True)


def write_pages(out, r):
    def table(headers, rows):
        return '<table><thead><tr>' + ''.join(f'<th>{html.escape(str(v))}</th>' for v in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{html.escape(str(v))}</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table>'
    def page(file, title, subtitle, content):
        document = '''<!doctype html><html lang="ko"><meta charset="utf-8"><title>''' + title + '''</title><style>
body{background:#f3f5f8;color:#182532;font:17px/1.65 -apple-system,BlinkMacSystemFont,sans-serif;margin:0;padding:32px}main{max-width:1080px;margin:auto;background:white;padding:32px 40px;border-radius:16px}h1{font-size:30px;line-height:1.35;margin:8px 0 14px}h2{font-size:22px;margin-top:28px}.eyebrow{font-size:14px;color:#3264aa;letter-spacing:.06em}p{color:#415264}table{border-collapse:collapse;width:100%;font-size:15px;margin:16px 0}th,td{padding:10px 12px;border-bottom:1px solid #dbe2ea;text-align:left}th{background:#eaf0f8}code,pre{background:#f1f4f8;border-radius:6px}pre{padding:20px;font-size:14px;white-space:pre-wrap;line-height:1.65}a{color:#3264aa}.note{background:#f2f5f9;padding:16px 20px;border-left:4px solid #7297c5}.stats{display:flex;gap:16px;margin:24px 0}.stat{background:#eef4fb;padding:16px 24px;flex:1}.stat b{display:block;font-size:28px}footer{margin-top:28px;font-size:13px;color:#637387}nav{display:flex;gap:20px;font-size:14px}</style><main><nav><a href="04-conversion.html">변환</a><a href="05-lightening.html">경량화</a><a href="06-verification.html">검증</a></nav><p class="eyebrow">ONTOLOGY LOCAL LAB · SYNTHETIC DATA</p><h1>''' + title + '</h1><p>' + subtitle + '</p>' + content + '<footer>실제 로컬 실행의 results.json으로 생성 · RDFS · RDFLib ' + r['environment']['packages']['rdflib'] + ' · 합성 자료 ' + f"{r['records']:,}" + '건 · 산업 규모 성능 검증 아님</footer></main></html>'
        (out / file).write_text(document, encoding='utf8')
    def stats(items):
        return '<div class="stats">' + ''.join(f'<div class="stat">{label}<b>{value:,}</b></div>' for label, value in items) + '</div>'
    page('04-conversion.html', 'CSV를 의미가 있는 RDF 그래프로 변환하기', '식별자 · 클래스 계층 · 작성자 · 주제 · 원천 행을 함께 보존한다.',
         stats([('CSV 물리 행', r['physical_csv_rows']), ('고유 자료', r['records']), ('명시적 트리플', r['explicit_triples_with_schema'])]) +
         '<h2>정의와 사실을 연결한 추론</h2><pre>Article ⊑ TextResource ⊑ LearningResource\nresource_00000 rdf:type Article\n\nRDFS closure 이후\nresource_00000 rdf:type TextResource\nresource_00000 rdf:type LearningResource</pre>' +
         table(['질문', '전체 RDFS 결과 수'], [[q, next(c['count'] for c in r['answer_checks'] if c['variant'] == 'full_rdfs' and c['query'] == q)] for q in QUERIES]) +
         '<p class="note">동일 레코드의 반복 입력은 고유 ID로 합친다. 제목이 같은 resource_00000과 resource_00001은 별개 개체로 유지한다. 작성자 누락은 SHACL 검증 대상으로 남긴다.</p>')
    page('05-lightening.html', '저장 표현과 데이터 범위를 따로 줄이기', '물리적 압축은 같은 그래프를 복원하고, 부분 선택은 대상 범위를 바꾼다.',
         table(['표현', '파일 바이트', '복원 그래프 동일'], [[s['format'], f"{s['bytes']:,}", s['graph_equal']] for s in r['storage']]) +
         stats([('전체 명시적 트리플', r['explicit_triples_with_schema']), ('주제 0 명시적 트리플', r['partial_explicit_triples']), ('주제 0 자료', r['selected_records'])]) +
         '<h2>선택적 타입 구체화</h2>' + table(['표현', '트리플 수'], [['전체 RDFS closure', r['rdfs_triples']], ['등록 질의용 타입만 추가', r['selective_type_triples']]]) +
         '<p class="note">gzip은 해제 후 파싱한다. 주제 0 부분 그래프는 선택한 자료의 작성자·주제·원천 행을 포함한다. 이는 ABox 범위 선택이며 논리적 TBox 모듈 추출이 아니다.</p>')
    rows = []
    for v in ['gzip_restored_rdfs', 'selective_types', 'topic_0_rdfs', 'removed_provenance_rdfs', 'broken_hierarchy_rdfs']:
        checks = [c for c in r['answer_checks'] if c['variant'] == v]
        rows.append([v] + [('같음' if c['same_global_answers'] else f"누락 {c['missing']:,} / 추가 {c['extra']:,}") for c in checks])
    page('06-verification.html', '작아진 결과가 같은 질문에 답하는지 검증하기', '정상 변환과 의도적으로 만든 손실 사례를 전체 결과 집합으로 비교한다.',
         table(['변환', 'Q1 주제', 'Q2 전체', 'Q3 누락', 'Q4 출처', 'Q5 계층'], rows) +
         '<h2>선택 범위와 검증 보고서</h2>' +
         '<p>주제 0으로 범위를 고정하면 Q1~Q5 모두 결과가 일치한다. 전역 범위에서는 일부 답이 빠진다.</p>' +
         table(['변환', 'SHACL 위반 수', 'conforms'], [[name, len(v['violations']), v['conforms']] for name, v in r['shacl'].items()]) +
         '<p class="note">검증 실패는 의도적으로 포함한 작성자 누락의 결과다. 압축 복원과 선택적 타입 구체화는 동일한 위반 목록을 유지한다. 이 검사는 등록한 질문에 대한 실험이며 모든 OWL 추론의 동치성 증명이 아니다.</p>')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--records', type=int, default=1000)
    p.add_argument('--repeats', type=int, default=3)
    args = p.parse_args()
    if args.records < 20 or args.repeats < 2:
        p.error('Use at least 20 records and 2 repeats.')
    run(args.records, args.repeats)
