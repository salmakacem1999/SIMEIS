import os
import sys
import json
import requests

IGNORED_LINES = [
    "TO" + "DO",
    "FIXME",
]

MDATA_KEYS = ["summary", "returns"]

def check_all_metadata(trace, mdata):
    for k in MDATA_KEYS:
        if k not in mdata:
            print("")
            print(f"ERROR: Metadata from {trace} is missing key {k}")
            print("")
            sys.exit(1)

def get_url_params(path):
    idx = 0
    result = []
    while "{" in path[idx:]:
        next_idx = idx + 1 + path[idx:].find("{")
        assert next_idx >= 0
        idx_end = next_idx + path[next_idx:].find("}")
        assert idx_end >= 0
        param = path[next_idx:idx_end]
        result.append(param)
        idx = idx_end + 1
    return result

def get_metadata(comments):
    mdata = {}
    doc = ""
    for commentraw in comments:
        comment = commentraw.removeprefix("//").strip()
        ismdata = False
        for key in MDATA_KEYS:
            if "@" + key in comment:
                mdata[key] = comment.removeprefix("@" + key).strip()
                ismdata = True
        if not ismdata:
            doc += comment + "\n"
    return (mdata, doc.strip())

def get_version(cargo_toml_file):
    with open(cargo_toml_file, "r") as f:
        cargotoml = f.read()
    for line in cargotoml.split("\n"):
        if "version" in line:
            return line.split("=")[1].strip().strip('"')
    raise Exception("Version not found in cargo.toml")

def get_comments_before(data, tag):
    result = []
    for (nline, line) in enumerate(data):
        line = line.strip()
        if tag in line:
            if any(["@noswagger" in l for l in result]):
                result = []
                continue
            mdata, doc = get_metadata(result)
            return (nline, mdata, doc)
        elif line.startswith("//") and all([s not in line for s in IGNORED_LINES]):
            result.append(line)
        else:
            result = []
    return None

class ApiChecker:
    def __init__(self, host, port, root):
        self.host = host
        self.port = port
        self.root = root
        self.examples = {}
        version = get_version(os.path.join(root, "../Cargo.toml"))
        with open(os.path.join(root, "main.rs"), "r") as f:
            main = f.read().split("\n")
        _, mdata, description = get_comments_before(main, "#[ntex::main]")
        assert description is not None
        self.swagger = {
            "openapi": "3.0.4",
            "info": {
                "title": "Simeis",
                "description": description,
                "version": version,
            },
            "servers": {},
            "paths": {},
        }
        self.swagger["info"].update(mdata)
        assert self.get("/ping")["error"] == "ok"

    def get(self, path, timeout=5):
        headers = {}
        if hasattr(self, "key"):
            headers["Simeis-Key"] = str(self.key)
        url = f"http://{self.host}:{self.port}/{path}"
        got = requests.get(url, headers=headers, timeout=timeout)
        assert got.status_code == 200
        return json.loads(got.text)

    def post(self, path, timeout=5):
        headers = {}
        if hasattr(self, "key"):
            headers["Simeis-Key"] = str(self.key)
        url = f"http://{self.host}:{self.port}/{path}"
        got = requests.post(url, headers=headers, timeout=timeout)
        assert got.status_code == 200
        return json.loads(got.text)

    def crawl(self):
        with open(os.path.join(self.root, "api.rs"), "r") as f:
            rootapi = [line for line in f.read().split("\n") if "::configure" in line]

        for section in rootapi:
            section_name = section.split("::configure")[0].strip()
            if section_name == "system":
                path = ""
            else:
                path = section.split("\"")[1]
            self.crawl_section(section_name, [path])

    def crawl_section(self, name, paths):
        print("Crawling {} (root path {})".format(name, "/".join(paths)))
        fpath = os.path.join(self.root, "api", name) + ".rs"
        with open(fpath, "r") as f:
            code = f.read().split("\n")

        self.crawl_for_method("get", name, code, "/".join(paths))
        self.crawl_for_method("post", name, code, "/".join(paths))

        for line in code:
            line = line.lstrip()
            if line.startswith(".configure(|srv|"):
                name = line.split("::configure(\"")[0].split("::")[-1]
                path = line.split("::configure(\"")[1].split("\"")[0].lstrip("/")
                self.crawl_section(name, paths + [ path ])

    def crawl_for_method(self, method, tag, code, rootpath):
        while True:
            got = get_comments_before(code, "#[web::" + method.lower())
            if got is None:
                return
            nline, mdata, doc = got
            path = rootpath + code[nline].split("\"")[1]
            all_params = get_url_params(path)
            name = code[nline+1].split("(")[0].split(" ")[-1]
            print("Found {} {} API {} at line {}".format(method.upper(), path, name, nline))
            check_all_metadata(f"{method.upper()}:{name}", mdata)
            data = {
                "description": doc,
                "responses": {
                    "200": {
                        "description": mdata.pop("returns"),
                    },
                },
                "tags": [ tag ],
                "parameters": [{
                    "name": n,
                    "in": "path",
                    "required": True,
                } for n in all_params]
            }
            data.update(mdata)
            self.swagger["paths"][path] = { method: data }
            code = code[nline+1:]
            # TODO Call API to get an example

    def check_rust_sdk(self):
        pass

    def check_python_sdk(self):
        pass

    def check_func_tests(self):
        pass

    def generate_html_file(self, proj, outfile):
        with open(os.path.join(proj, ".swagger/swagger-ui.css"), "r") as f:
            swaggercss = f.read()
        with open(os.path.join(proj, ".swagger/swagger-ui-bundle.js"), "r") as f:
            swaggerbundle = f.read()
        with open(os.path.join(proj, ".swagger/swagger-ui-standalone-preset.js"), "r") as f:
            swaggerpreset = f.read()
        with open(os.path.join(proj, ".swagger/swagger-initializer.js"), "r") as f:
            swaggerinit = f.read()
        swaggerui = f"<style>{swaggercss}</style>"
        swaggerui += f"<script>{swaggerbundle}</script>"
        swaggerui += f"<script>{swaggerpreset}</script>"
        swaggerui += f"<script>{swaggerinit}</script>"
        swaggerui += "<div id=\"ui\"></div>"

        with open(outfile, "w") as f:
            f.write("<html><head>")
            f.write("<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">")
            f.write(f"</head><body>{swaggerui}</body></html>")
        pass

    def generate_swagger(self, outfile):
        with open(outfile, "w") as f:
            json.dump(self.swagger, f, indent=2)

    def prepare_examples(self):
        # TODO Prepare a game so I can make actions later
        # TODO Add some of the data got from API to self.examples
        pass

ip = sys.argv[1]
port = sys.argv[2]

proj = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
rootd = os.path.join(proj, "simeis-server/src")

checker = ApiChecker(ip, port, rootd)
checker.prepare_examples()
checker.crawl()
checker.check_rust_sdk()
checker.check_python_sdk()
checker.check_func_tests()
checker.generate_swagger(os.path.join(proj, "doc/swagger.json"))
checker.generate_html_file(proj, os.path.join(proj, "doc/swagger-ui.html"))
