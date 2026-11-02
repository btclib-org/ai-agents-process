# shellcheck shell=sh
# The measure of /btclib-table, which only reads. SKILL.md, beside this
# file, says what its output means. Run it as:
#
#   sh "${PROCESS:?}/skills/btclib-table/measure.sh"
#
# each repository's row goes to "${d}/<repo>.row" and its counts to
# "${d}/<repo>.tot" ("<iss> <prs>", or "err")
d=$(mktemp -d)
trap 'rm -r "${d}"' EXIT
trap 'exit 1' INT TERM
w="${d}/row.sh"
cat > "${w}" <<'EOF_ROW'
# call: a command's output, or "error: <its stderr>" and exit 1 where it
# fails or prints anything on stderr
call() {
  e=$(mktemp "${d}/err.XXXXXX")
  o=$("$@" 2> "${e}")
  s=$?
  if [ "${s}" -ne 0 ] || [ -s "${e}" ]; then
    printf 'error: %s' "$(tr '\n' ' ' < "${e}")"
    rm -f "${e}"
    return 1
  fi
  rm -f "${e}"
  printf '%s' "${o}"
}
r=$1
# given a workflow id too: that workflow's ci entry, into "${d}/<repo>.wf.<id>"
if [ $# -gt 1 ]; then
  c=$(call gh api -X GET "repos/btclib-org/${r}/actions/workflows/${2}/runs" \
    -f branch=main -f status=completed -f per_page=20 \
    --jq "[.workflow_runs[] | select(.head_repository.full_name
      == \"btclib-org/${r}\" and .conclusion != \"cancelled\")][0] // empty
      | select(.conclusion | IN(\"success\", \"skipped\") | not)
      | .name + \"=\" + .conclusion") || c="${2}=${c}"
  printf '%s' "${c}" > "${d}/${r}.wf.${2}"
  exit 0
fi
{
  iss=$(call gh issue list -R "btclib-org/${r}" --state open --limit 1000 \
    --json number --jq length)
  prs=$(call gh pr list -R "btclib-org/${r}" --state open --limit 1000 \
    --json number --jq length)
  case ${iss}${prs} in
    *[!0-9]*) echo err > "${d}/${r}.tot" ;;
    *) echo "${iss} ${prs}" > "${d}/${r}.tot" ;;
  esac
  printf '%s' "iss=${iss} | pr=${prs}"
} > "${d}/${r}.counts" &
{
  ci="" wfs=$(call gh api \
    "repos/btclib-org/${r}/actions/workflows?per_page=100" \
    --jq '.workflows[] | select(.state == "active")
      | select(.path != ".github/workflows/release.yml") | .id') ||
    ci="${wfs}"
  if [ -z "${ci}" ] && [ -n "${wfs}" ]; then
    ids=$(printf '%s' "${wfs}" | paste -sd, -)
    page=$(call gh api -X GET "repos/btclib-org/${r}/actions/runs" \
      -f branch=main -f status=completed -f per_page=100 \
      --jq "[${ids}] as \$ids | .total_count as \$t | .workflow_runs as \$runs
        | \$ids[] as \$w
        | [\$runs[] | select(.workflow_id == \$w)] as \$mine
        | [\$mine[:20][] | select(.head_repository.full_name
            == \"btclib-org/${r}\" and .conclusion != \"cancelled\")][0] as \$c
        | \"\(\$w)\t\" + if \$c != null then
            (if \$c.conclusion | IN(\"success\", \"skipped\") then \"\"
             else \"\(\$c.name)=\(\$c.conclusion)\" end)
          elif (\$mine | length) >= 20 or \$t <= (\$runs | length) then \"\"
          else \"?\" end") || page=""
    # the workflows the page does not settle, or all where it failed, read
    # eight at a time; the loop after it keeps the workflows' order
    printf '%s\n' "${page:-$wfs}" | while read -r w c; do
      if [ -n "${w}" ] && { [ "${c}" = "?" ] || [ -z "${page}" ]; }; then
        echo "${w}"
      fi
    done > "${d}/${r}.todo"
    [ ! -s "${d}/${r}.todo" ] ||
      xargs -n 1 -P 8 sh "$0" "${r}" < "${d}/${r}.todo"
    while read -r w c; do
      [ -n "${w}" ] || continue
      [ ! -f "${d}/${r}.wf.${w}" ] || c=$(cat "${d}/${r}.wf.${w}")
      [ -z "${c}" ] || ci="${ci:+${ci},}${c}"
    done <<EOF_WFS
${page:-$wfs}
EOF_WFS
  fi
  printf '%s' "${ci:-ok}"
} > "${d}/${r}.ci" &
{
  rel=no
  gh api "repos/btclib-org/${r}/contents/.github/workflows/release.yml" \
    > /dev/null 2>&1 && rel=yes
  printf '%s' "${rel}"
} > "${d}/${r}.rel" &
{
  tag=$(gh api "repos/btclib-org/${r}/tags?per_page=100" --jq '.[].name' \
    2>/dev/null | sort -V | tail -n 1)
  since=""
  [ -n "${tag}" ] && since=$(gh api \
    "repos/btclib-org/${r}/compare/${tag}...HEAD" --jq '
      .base_commit.commit.committer.date[:10] + " | since: "
      + ([.commits[].commit.message | split("\n")[0]] | join(" || "))' \
    2>/dev/null)
  printf '%s' "tag=${tag:-none} ${since}"
} > "${d}/${r}.tag" &
badges="" readme=$(call gh api "repos/btclib-org/${r}/readme" \
  -H 'Accept: application/vnd.github.raw') || case ${readme} in
  *"(HTTP 404)"*) readme="" ;;
  *) badges="${readme}" readme="" ;;
esac
bp=$(printf '%s' "${readme}" |
  grep -oE 'bestpractices\.dev/projects/[0-9]+' | head -n 1 | sed 's|.*/||')
pkg=$(gh api "repos/btclib-org/${r}/contents/pyproject.toml" \
    -H 'Accept: application/vnd.github.raw' 2>/dev/null |
  uv run --no-project --python 3.15 python -c '
import json, sys, tomllib, urllib.request
try:
    p = tomllib.loads(sys.stdin.read()).get("project", {})
except Exception:
    p = {}
name, pypi = p.get("name", "-"), "-"
if name != "-":
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        page = urllib.request.urlopen(url, timeout=10)
        pypi = json.load(page)["info"]["version"]
    except Exception:
        pass
deps = ", ".join(p.get("dependencies", [])) or "-"
r, bp = sys.argv[1:]
bl3 = gold = "-"
if bp:
    url = f"https://www.bestpractices.dev/projects/{bp}.json"
    try:
        b = json.load(urllib.request.urlopen(url, timeout=10))
        url_seen = b["repo_url"]
        if url_seen.rstrip("/").split("/")[-1] not in (r, name):
            bl3 = gold = f"mismatch: {url_seen}"
        else:
            bl3 = b["badge_percentage_baseline_3"]
            gold = b["badge_percentage_2"]
    except Exception as e:
        msg = " ".join(f"{type(e).__name__}: {e}".split())
        bl3 = gold = f"error: {msg}"
print(f"{name} | pypi={pypi} | bl3={bl3} gold={gold} | deps: {deps}")' \
  "${r}" "${bp}")
[ -n "${badges}" ] || badges=$(printf '%s' "${readme}" |
  uv run --no-project --python 3.15 python -c '
import colorsys, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor


def check(url):
    req = urllib.request.Request(url, headers={"User-Agent": "btclib-table"})
    try:
        svg = urllib.request.urlopen(req, timeout=10).read().decode()
    except Exception as e:
        return f"{url}: {e}"
    title = (re.findall(r"<title>([^<]*)", svg) or [url])[0]
    if re.fullmatch(r"openssf best practices: (silver|gold)", title):
        return None
    hues = []
    hexes = r"(?:fill|stop-color)=.#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\W"
    for h in re.findall(hexes, svg):
        h = "".join(c * 2 for c in h) if len(h) == 3 else h
        rgb = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
        hue, sat, _ = colorsys.rgb_to_hsv(*rgb)
        if sat >= 0.5:
            hues.append(hue * 360)
    if not hues or not all(70 <= hue < 260 for hue in hues):
        return title
    return None


urls = re.findall(r"!\[[^]]*\]\(([^)\s]+)", sys.stdin.read())
urls = [u for u in urls if "/pypi/status/" not in u]
with ThreadPoolExecutor(8) as pool:
    bad = [b for b in pool.map(check, urls) if b]
print(" || ".join(bad))') || badges="error: the badge script failed"
wait
printf '%s\n' "${r} | $(cat "${d}/${r}.counts") | ${pkg}\
 | release.yml=$(cat "${d}/${r}.rel") | ci=$(cat "${d}/${r}.ci")\
 | badges=${badges:-ok} | $(cat "${d}/${r}.tag")" > "${d}/${r}.row"
EOF_ROW
export d
gh repo list btclib-org --no-archived --limit 200 \
    --json name --jq '.[].name' | sort > "${d}/repos"
xargs -n 1 -P 6 sh "${w}" < "${d}/repos"
ti=0 tp=0 part=""
while read -r r; do
  cat "${d}/${r}.row"
  i=err
  read -r i p < "${d}/${r}.tot"
  case ${i} in
    err) part=" (rows with an error left out)" ;;
    *) ti=$(( ti + i )) tp=$(( tp + p )) ;;
  esac
done < "${d}/repos"
echo "total | iss=${ti} | pr=${tp}${part}"
