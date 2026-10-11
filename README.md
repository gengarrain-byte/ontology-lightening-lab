# 온톨로지 경량화 실습 자료

CSV를 RDF로 변환하고 경량화 전후에 같은 질문에 답할 수 있는지 비교하는 독립된 학습 예제입니다. 모든 자료는 프로그램으로 만든 합성 데이터입니다.

먼저 20건으로 구조를 살펴보고, 글의 캡처와 비교하려면 1,000건을 실행하면 됩니다. 5,000건은 같은 변환을 조금 더 큰 입력으로 반복하는 자료입니다. 이 세 규모는 운영 환경의 대용량 성능 벤치마크가 아닙니다.

저장소 상단의 **Code → Download ZIP**으로 전체 자료를 받습니다. CSV만 필요하다면 해당 파일을 열어 **Raw**로 저장할 수 있습니다.

## Medium 공부 글

온톨로지 경량화 공부를 여섯 편으로 정리했습니다. **현재 모두 퇴고 중인 미게시 초안입니다. 아래 읽기 링크는 글을 공개한 뒤 이용할 수 있습니다.**

| 편 | 내용 | Medium |
| --- | --- | --- |
| 1 | 파일 크기만 줄이면 될까 | [읽기](https://medium.com/p/497e0088da64) |
| 2 | 공리를 줄일까 데이터를 줄일까 | [읽기](https://medium.com/p/864c47c51afb) |
| 3 | 작아진 그래프에서 사라진 답 찾기 | [읽기](https://medium.com/p/6bb29a46886a) |
| 4 | CSV를 RDF 그래프로 옮겨 보기 | [읽기](https://medium.com/p/edc0073b6ff6) |
| 5 | 같은 그래프로 세 가지 실험하기 | [읽기](https://medium.com/p/892a4539be5d) |
| 6 | 줄인 뒤에도 같은 답이 나오는지 확인하기 | [읽기](https://medium.com/p/1007ee5729d3) |

1–3편은 개념과 보존 기준을 정리하고, 4–6편은 이 저장소의 데이터를 변환하고 결과를 비교합니다.

## 파일 구성

파일 이름을 누르면 저장소에서 내용을 확인할 수 있습니다.

| 파일 | 담긴 내용 | 사용할 때 |
| --- | --- | --- |
| [README.md](README.md) | 공부 글 링크, 파일 설명, 실행 순서와 결과 해석 | 처음 시작할 때 |
| [run_lab.py](run_lab.py) | CSV 생성 → RDF 변환 → 추론 → 경량화 → 질의·SHACL 비교 → 결과 화면 생성 | 실습 전체를 실행할 때 |
| [requirements.txt](requirements.txt) | RDFLib 7.1.4, OWL-RL 7.1.4, pySHACL 0.30.1 버전 | Python 패키지를 설치할 때 |
| [ontology.ttl](ontology.ttl) | 학습 자료·글·강의·작성자·주제·출처의 정의와 클래스 계층 | RDF 변환과 RDFS 추론의 기준을 읽거나 수정할 때 |
| [shapes.ttl](shapes.ttl) | LearningResource에 작성자·제목·원천 연결이 있어야 한다는 SHACL 규칙 | 누락 데이터를 검증할 때 |
| [source-20.csv](source-20.csv) | 고유 자료 20건, 반복 행을 포함한 물리 입력 22행 | 작은 입력을 직접 읽어 볼 때 |
| [source-1000.csv](source-1000.csv) | 고유 자료 1,000건, 물리 입력 1,059행 | 글의 결과와 같은 규모를 확인할 때 |
| [source-5000.csv](source-5000.csv) | 고유 자료 5,000건, 물리 입력 5,295행 | 자료 수를 늘려 같은 구조를 비교할 때 |
| [graph-20.ttl](graph-20.ttl) | 20건을 변환한 명시적 RDF 그래프, 정의 포함 163트리플 | CSV 한 행이 어떤 사실로 변환됐는지 읽을 때 |
| [graph-1000.ttl](graph-1000.ttl) | 1,000건을 변환한 명시적 RDF 그래프, 정의 포함 6,034트리플 | 경량화 전의 그래프를 살펴볼 때 |
| [topic-0-1000.ttl](topic-0-1000.ttl) | 주제 0의 167건과 작성자·주제·원천 연결·정의, 1,031트리플 | 전체 그래프와 선택 범위의 차이를 볼 때 |
| [selective-types-1000.ttl](selective-types-1000.ttl) | 명시적 그래프에 LearningResource·TextResource 타입만 추가한 7,534트리플 | 필요한 추론 결과만 저장한 사례를 볼 때 |
| [Q1_topic_0.rq](Q1_topic_0.rq) | 주제 0에 연결된 자료를 찾는 SPARQL 질의 | 주제 선택이 답을 유지하는지 검사할 때 |
| [Q2_resources.rq](Q2_resources.rq) | LearningResource 타입의 전체 자료를 찾는 질의 | 상위 타입 추론과 전체 자료 수를 검사할 때 |
| [Q3_missing_author.rq](Q3_missing_author.rq) | LearningResource 중 작성자 관계가 없는 자료를 찾는 질의 | 누락 사례가 그대로 남았는지 검사할 때 |
| [Q4_provenance.rq](Q4_provenance.rq) | 자료·원천 레코드·CSV 행 번호를 함께 찾는 질의 | 출처 연결이 사라졌는지 검사할 때 |
| [Q5_text_resources.rq](Q5_text_resources.rq) | TextResource 타입의 글을 찾는 질의 | Article의 클래스 계층을 바꿨을 때 답이 달라지는지 검사할 때 |
| [expected-20.json](expected-20.json) | 20건 실행의 트리플 수, 질의 비교, 위반 목록, 측정 조건 | 작은 실행의 결과 기준을 확인할 때 |
| [expected-1000.json](expected-1000.json) | 원고와 캡처에 사용한 1,000건 실행 기록 | 글의 숫자와 재실행 결과를 비교할 때 |
| [expected-5000.json](expected-5000.json) | 5,000건 실행 기록 | 규모를 늘린 반복 실험을 확인할 때 |
| [04-conversion.jpg](04-conversion.jpg) | 1,000건 CSV → RDF 변환 결과 캡처 | 4편 실습 결과를 미리 볼 때 |
| [05-lightening.jpg](05-lightening.jpg) | 저장 표현·부분 선택·선택적 타입 저장 결과 캡처 | 5편의 세 실험을 비교할 때 |
| [06-verification.jpg](06-verification.jpg) | 질의 결과와 SHACL 위반 비교 캡처 | 6편의 보존·손실 검사를 볼 때 |
| [materials-manifest.json](materials-manifest.json) | 자신을 제외한 제공 파일의 바이트 수와 SHA-256 | 받은 파일의 무결성을 확인할 때 |
| [.gitignore](.gitignore) | 가상환경·캐시·재실행 결과 폴더 제외 규칙 | 로컬 실행 결과가 실수로 커밋되는 것을 막을 때 |

## 데이터에서 확인할 사례

CSV의 열은 id, kind, title, author, topic입니다. id는 자료의 식별자이고 kind는 Article 또는 Course입니다. 작성자와 주제는 각각 사람·주제 개체의 ID로 해석합니다.

- 같은 ID와 내용이 반복되는 행이 있습니다. 첫 번째 물리 행을 원천 위치로 기록하고 반복 입력은 한 자료로 변환합니다.
- resource_00000과 resource_00001은 제목이 같지만 서로 다른 자료입니다. 제목으로 중복을 판단하면 안 됩니다.
- 작성자 값이 비어 있는 자료가 있습니다. SHACL에서 위반으로 남아야 하는 의도적인 입력입니다.
- Article → TextResource → LearningResource와 Course → LearningResource 계층을 조회합니다.
- 주제 0만 선택했을 때 전체 답의 범위가 어떻게 줄어드는지 확인합니다.
- 출처 연결 제거와 클래스 공리 제거는 코드가 실행 중 별도의 그래프에 만드는 손실 사례입니다. 원천 CSV를 손상시키지는 않습니다.

이 CSV는 같은 ID의 서로 다른 내용을 다루는 충돌 처리 예제가 아닙니다. 반복 행은 내용이 같고 코드는 첫 번째 ID를 유지합니다. 원천 행 번호는 헤더를 1행으로 센 해당 생성 CSV의 위치입니다.

## 사용법

### 1. 자료 내려받기

**Code → Download ZIP**으로 받은 ZIP을 풀고 터미널에서 압축을 푼 저장소 폴더로 이동합니다. README.md, run_lab.py, ontology.ttl이 같은 위치에 있어야 합니다.

### 2. 환경 준비와 실행

Python 3.12 환경에서 ZIP을 풀고 이 파일들이 있는 디렉터리에서 실행합니다. 명령은 macOS·Linux 기준입니다. 원고의 실행 환경은 Python 3.12.14, rdflib 7.1.4, owlrl 7.1.4, pyshacl 0.30.1이었습니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_lab.py --records 20 --repeats 3
.venv/bin/python run_lab.py --records 1000 --repeats 3
.venv/bin/python run_lab.py --records 5000 --repeats 3
```

Windows에서는 같은 폴더의 PowerShell에서 다음 순서로 실행할 수 있습니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_lab.py --records 20 --repeats 3
.\.venv\Scripts\python.exe run_lab.py --records 1000 --repeats 3
```

--records는 고유 자료 수이며 최소 20, --repeats는 warm 질의 시간의 반복 측정 수이며 최소 2입니다. 생략하면 각각 1,000과 3으로 실행합니다. 첫 실행은 20건으로 시작하고, 1,000건 실행을 글의 캡처와 비교하면 됩니다.

run_lab.py는 동일한 생성 규칙으로 원천 CSV를 다시 만들고 run-20, run-1000, run-5000 폴더에 변환 결과를 저장합니다. 제공한 source-N.csv는 실행 당시의 입력 사본입니다. 해당 CSV를 직접 수정해 실험하려면 스크립트의 원천 생성 단계와 CSV 읽기 단계를 분리해야 합니다. 수정된 CSV가 자동으로 입력되는 명령이라고 해석하지 마세요.

같은 자료 수로 다시 실행하면 해당 run-N 폴더의 파일을 다시 작성합니다. 보관된 expected-N.json은 작성 당시 실행 기록이므로 입력 사본과 함께 유지하는 편이 좋습니다.

### 3. 생성된 파일 확인

1,000건을 실행하면 run-1000 폴더에 다음 파일이 생깁니다. 20건과 5,000건은 각각 run-20, run-5000에 같은 이름으로 저장됩니다.

| 생성 파일 | 확인할 내용 |
| --- | --- |
| source.csv | 이번 실행에서 생성한 원천 CSV |
| graph.ttl, graph.nt, graph.rdf | 같은 명시적 그래프의 Turtle·N-Triples·RDF/XML 표현 |
| graph.ttl.gz | Turtle의 gzip 압축본; 질의 전 해제 필요 |
| topic-0.ttl | 주제 0의 자료와 지원 연결을 선택한 명시적 그래프 |
| selective-types.ttl | 두 상위 타입만 추가해 보관한 그래프 |
| Q1_topic_0.rq부터 Q5_text_resources.rq까지 | 실행에서 사용하는 다섯 SPARQL 질의 |
| results.json | 이번 실행의 수량, 전체 결과 집합 비교, SHACL 위반, 측정 환경 |
| 04-conversion.html | 변환 결과 요약 화면 |
| 05-lightening.html | 경량화 실험 요약 화면 |
| 06-verification.html | 질의와 SHACL 검증 요약 화면 |

results.json의 answer_checks에서 variant별로 count, same_global_answers, missing, extra를 확인합니다. scope_checks는 주제 0으로 범위를 맞춘 답의 비교이고, shacl은 위반 목록입니다. expected-N.json과 시간·바이트 수까지 완전히 같아야 하는 비교는 아닙니다.

## 예상 결과

| 자료 수 | 반복 행 | 명시적 트리플 | RDFS 확장 트리플 | Q1 주제 0 | Q2 전체 자료 | Q3 작성자 누락 | Q4 출처 | Q5 글 | SHACL 위반 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | 2 | 163 | 397 | 4 | 20 | 1 | 20 | 10 | 1 |
| 1,000 | 59 | 6,034 | 12,641 | 167 | 1,000 | 11 | 1,000 | 500 | 11 |
| 5,000 | 295 | 29,993 | 62,600 | 834 | 5,000 | 52 | 5,000 | 2,500 | 52 |

SHACL의 conforms=false는 의도적으로 남긴 작성자 누락의 결과입니다. 압축 복원과 선택적 타입 저장은 같은 질의 결과와 같은 위반 목록을 유지합니다. 주제 0의 부분 그래프는 전역 답과 다르지만 선택한 자료의 범위에서는 다섯 질의의 결과가 같습니다.

출처를 제거하면 Q4의 답이 사라지고, Article이 TextResource의 하위 클래스라는 공리를 제거하면 Q5에서 글이 빠지는지도 검사합니다. 프로그램이 끝까지 실행됐다는 것은 손실 사례가 예상대로 검출되는 검사도 통과했다는 뜻입니다.

## 결과 화면

### 4. 브라우저에서 결과 보기

실행 후 이 디렉터리에서 다음 서버를 시작합니다.

```bash
python3 -m http.server 18769 --bind 127.0.0.1
```

- 변환: http://127.0.0.1:18769/run-1000/04-conversion.html
- 경량화: http://127.0.0.1:18769/run-1000/05-lightening.html
- 검증: http://127.0.0.1:18769/run-1000/06-verification.html

Windows에서는 서버 명령의 `python3` 대신 `.\.venv\Scripts\python.exe`를 사용합니다. 확인을 마치면 서버를 실행한 터미널에서 Ctrl+C로 종료합니다.

이 페이지들은 실제 실행 결과를 표시하는 요약 화면입니다. Medium 4–6편의 캡처는 원고 작성 당시 1,000건 실행 화면에서 남겼습니다.

### 변환

![CSV를 RDF로 변환한 결과](04-conversion.jpg)

### 경량화

![같은 그래프를 세 가지 방식으로 줄인 결과](05-lightening.jpg)

### 검증

![경량화 전후 질의와 SHACL 검증 결과](06-verification.jpg)

## 비교할 때 주의할 측정 범위

파일 바이트는 DB 저장량이나 heap 측정값이 아닙니다. gzip은 압축을 푼 뒤 파싱합니다. 직렬화 순서에 따라 재실행한 파일 크기와 압축 크기가 달라질 수 있어 바이트 크기와 시간 측정값을 합격 기준으로 사용하지 않습니다.

선택적 타입 저장은 전체 RDFS 결과를 먼저 계산한 뒤 필요한 타입을 고릅니다. 조회 시간은 준비된 메모리 그래프에서 결과를 끝까지 읽는 warm 측정이며 적재·질의 준비·추론 시간을 제외합니다.

이 실습은 RDFS 추론, ABox 범위 선택, 등록한 다섯 질의의 결과 비교입니다. 전체 OWL DL 추론, OWL 프로필 변환, 형식적 TBox 모듈 추출이나 모든 질의에 대한 동치성 증명으로 설명하지 않습니다.
