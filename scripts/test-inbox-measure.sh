#!/bin/sh
# What skills/btclib-inbox/measure.sh prints on answers written here:
#
#   sh scripts/test-inbox-measure.sh [<measure.sh>]
#
# A stand-in for gh, first on the PATH, serves each call from the case's
# files and applies the call's --jq filter to them with jq, as gh does.
# It reads the GraphQL query it is sent, from the file a `query=@<file>`
# names or from the argument, and drops each key of the answer's `data`
# whose name is not a word of the query: a field the query does not ask
# for is not served, though it is matched by name, not by where the
# query asks for it. A stand-in for sleep returns at once. Each case has
# an issue by an outside person with no reply, and the agent's pull
# request with the bot's ACK on its head, its checks green. The cases,
# in order:
#
# - ordinary: the pull request is mergeable. Exits 0, with the issue in
#   group 1, the pull request in group 4, and no unknown mergeability.
# - pages: the pull request search comes in two pages, whose items add up
#   to its count of matches. Exits 0, with both pull requests in group 4.
# - cut short: the issue search counts more matches than it returned, as
#   a search past GitHub's cap does. Exits 1 with `error: issues:`.
# - repeated: the pull request search returns one item on each of its
#   two pages, the same one, and counts two matches. Exits 1 with
#   `error: prs:`.
# - null count, no count, no page: the pull request search gives
#   `issueCount` as null, the issue search gives none, or the pull
#   request search gives no page at all. Each exits 1 with
#   `error: <search>: the search gave no count of matches`.
# - same head: the mergeability is unknown, and the second read finds it
#   mergeable on the same head. Exits 0, with the pull request in group 4.
# - still unknown: the second read finds it unknown again. Exits 0, with
#   the pull request in no group and linked on the last line.
# - head moved: the second read finds it mergeable on another head. Exits
#   0, with the pull request in no group and linked on the last line.
#
# Then the cases run again on two copies of measure.sh, each with one
# field taken out of its queries: `issueCount` from both searches, and
# `headRefOid` from the second read of a mergeability. A copy is caught,
# and prints `ok`, where some case fails on it.
#
# Each line it prints starts `ok` or `FAIL`; a failed case is followed by
# what measure.sh printed. It exits 1 where a case failed or a copy was
# not caught.
measure=${1:-$(dirname "$0")/../skills/btclib-inbox/measure.sh}
tmp=$(mktemp -d "${TMPDIR:-/tmp}/test-inbox-measure.XXXXXX") || exit 1
trap 'rm -rf "${tmp:?}"' EXIT
a=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
b=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
u=https://github.com/btclib-org/repo-a

mkdir "${tmp}/bin"
cat > "${tmp}/bin/gh" <<'EOF_GH'
#!/bin/sh
# gh, answering from "${FIX}"
what= f= q= query= r= n=
for x in "$@"; do
  case ${x} in
    user) what=user ;;
    graphql) what=graphql ;;
    repos/*) what=comments ;;
  esac
done
[ "$1" = repo ] && what=repos
while [ $# -gt 0 ]; do
  case $1 in
    --jq) f=$2; shift ;;
    -f | -F)
      case $2 in
        q=*) q=${2#q=} ;;
        query=*) query=${2#query=} ;;
        r=*) r=${2#r=} ;;
        n=*) n=${2#n=} ;;
      esac
      shift ;;
  esac
  shift
done
case ${query} in
  @*) query=$(cat "${query#@}") || exit 1 ;;
esac
case ${what}:${q}:${query} in
  user:*) file=user.json ;;
  repos:*) file=repos.json ;;
  comments:*) file=comments.json ;;
  graphql:*is:pr*) file=prs.json ;;
  graphql:*is:issue*) file=issues.json ;;
  graphql::*"pullRequest(number"*) file=merge.${r}.${n}.json ;;
  *) echo "gh stand-in: no answer for: $*" >&2; exit 1 ;;
esac
if [ "${what}" = graphql ]; then
  jq -c --arg q "${query}" '[$q | scan("[A-Za-z_][A-Za-z0-9_]*")] as $w
    | .data |= walk(if type == "object" then
        with_entries(select(.key as $k | any($w[]; . == $k))) else . end)' \
    "${FIX:?}/${file}"
else
  cat "${FIX:?}/${file}"
fi | if [ -n "${f}" ]; then jq -r "${f}"; else cat; fi
EOF_GH
printf '#!/bin/sh\n' > "${tmp}/bin/sleep"
chmod +x "${tmp}/bin/gh" "${tmp}/bin/sleep"

# pr <n> <head> <mergeable>: the agent's pull request, as the search
# returns it
pr() {
  jq -nc --argjson n "$1" --arg h "$2" --arg m "$3" --arg u "${u}" '{
    number: $n, title: "Pull \($n)", url: "\($u)/pull/\($n)",
    isDraft: false, additions: 2, deletions: 1, changedFiles: 1,
    repository: {name: "repo-a"}, author: {__typename: "Bot", login: "claude"},
    authorAssociation: "NONE",
    labels: {pageInfo: {hasNextPage: false}, nodes: []},
    reviewDecision: "REVIEW_REQUIRED", mergeable: $m, headRefOid: $h,
    commits: {nodes: [{commit: {committedDate: "2026-01-02T00:00:00Z",
      statusCheckRollup: {state: "SUCCESS"}}}]},
    reviewRequests: {pageInfo: {hasNextPage: false}, nodes: []},
    timelineItems: {nodes: []}, reviews: {nodes: []},
    verdicts: {nodes: [{body: "ACK \($h)\n\nNothing found."}]},
    comments: {nodes: []}}'
}
# an outside person's issue with no reply, as the search returns it
issue() {
  jq -nc --arg u "${u}" '{
    number: 3, title: "Issue 3", url: "\($u)/issues/3",
    createdAt: "2026-01-01T00:00:00Z", repository: {name: "repo-a"},
    author: {__typename: "User", login: "alice"}, authorAssociation: "NONE",
    labels: {pageInfo: {hasNextPage: false}, nodes: []},
    timelineItems: {nodes: []}, comments: {nodes: []}}'
}
# page <count> <has next page> <node>...: one page of a search
page() {
  pc=$1 px=$2
  shift 2
  printf '%s\n' "$@" | jq -sc --argjson c "${pc}" --argjson x "${px}" '{data:
    {search: {issueCount: $c, pageInfo: {hasNextPage: $x, endCursor: "e"},
      nodes: .}}}'
}
# merge <n> <head> <mergeable>: the second read of the pull request
merge() {
  jq -nc --argjson n "$1" --arg h "$2" --arg m "$3" --arg u "${u}" \
    '{data: {repository: {pullRequest:
      {url: "\($u)/pull/\($n)", mergeable: $m, headRefOid: $h}}}}'
}
# new <case>: the case's directory, with the answers every case shares
new() {
  mkdir "${tmp}/$1"
  echo '{"login": "maintainer"}' > "${tmp}/$1/user.json"
  echo '[{"name": "repo-a"}]' > "${tmp}/$1/repos.json"
  echo '[]' > "${tmp}/$1/comments.json"
  page 1 false "$(issue)" > "${tmp}/$1/issues.json"
  page 1 false "$(pr 7 "${a}" MERGEABLE)" > "${tmp}/$1/prs.json"
}

new ordinary
new pages
{ page 2 true "$(pr 7 "${a}" MERGEABLE)"
  page 2 false "$(pr 8 "${a}" MERGEABLE)"; } > "${tmp}/pages/prs.json"
new cut-short
page 1001 false "$(issue)" > "${tmp}/cut-short/issues.json"
new repeated
{ page 2 true "$(pr 7 "${a}" MERGEABLE)"
  page 2 false "$(pr 7 "${a}" MERGEABLE)"; } > "${tmp}/repeated/prs.json"
new null-count
page null false "$(pr 7 "${a}" MERGEABLE)" > "${tmp}/null-count/prs.json"
new no-count
page 1 false "$(issue)" | jq -c 'del(.data.search.issueCount)' \
  > "${tmp}/no-count/issues.json"
new no-page
: > "${tmp}/no-page/prs.json"
for c in same-head still-unknown head-moved; do
  new "${c}"
  page 1 false "$(pr 7 "${a}" UNKNOWN)" > "${tmp}/${c}/prs.json"
done
merge 7 "${a}" MERGEABLE > "${tmp}/same-head/merge.repo-a.7.json"
merge 7 "${a}" UNKNOWN > "${tmp}/still-unknown/merge.repo-a.7.json"
merge 7 "${b}" MERGEABLE > "${tmp}/head-moved/merge.repo-a.7.json"

fail=0
# run <case> <exit code> <text it holds, then -- and text it lacks>
run() {
  c=$1 want=$2 ok=1 rc=0
  shift 2
  env PATH="${tmp}/bin:${PATH}" FIX="${tmp}/${c}" TMPDIR="${tmp}/${c}" \
    sh "${measure}" > "${tmp}/${c}/out" 2>&1 || rc=$?
  if [ "${rc}" != "${want}" ]; then
    echo "FAIL ${c}: exit ${rc}, not ${want}"
    ok=0
  fi
  holds=1
  for l in "$@"; do
    if [ "${l}" = -- ]; then
      holds=0
    elif [ "${holds}" = 1 ] && ! grep -q -F -e "${l}" "${tmp}/${c}/out"; then
      echo "FAIL ${c}: lacks ${l}"
      ok=0
    elif [ "${holds}" = 0 ] && grep -q -F -e "${l}" "${tmp}/${c}/out"; then
      echo "FAIL ${c}: holds ${l}"
      ok=0
    fi
  done
  if [ "${ok}" = 1 ]; then
    echo "ok ${c}"
  else
    sed 's/^/  | /' "${tmp}/${c}/out"
    fail=1
  fi
}

# a row after its age, which is counted from now
iss="[ISS repo-a#3](${u}/issues/3) — alice's, no reply — Issue 3"
row() {
  echo "[PR repo-a#$1](${u}/pull/$1) 1 file, +2/-1 — ACK, needs your" \
    "approval — Pull $1"
}
unknown="; mergeability unknown: [PR repo-a#7](${u}/pull/7)"
cases() {
  run ordinary 0 "**A person waits on an answer**" "${iss}" \
    "**The bot's ACK, needs your approval**" "$(row 7)" -- \
    "mergeability unknown" "error:"
  run pages 0 "$(row 7)" "$(row 8)" -- "error:"
  short="the search was cut short"
  run cut-short 1 "error: issues: ${short}: 1001 matches, 1 returned"
  run repeated 1 "error: prs: ${short}: 2 matches, 1 returned"
  nocount="the search gave no count of matches"
  run null-count 1 "error: prs: ${nocount}"
  run no-count 1 "error: issues: ${nocount}"
  run no-page 1 "error: prs: ${nocount}"
  run same-head 0 "$(row 7)" -- "mergeability unknown"
  run still-unknown 0 "${unknown}" -- "ACK, needs your approval" "error:"
  run head-moved 0 "${unknown}" -- "ACK, needs your approval" "error:"
}
cases

# mutant <name> <sed script> <text it changes>: the cases on a copy of
# measure.sh the sed script changed, caught where a case fails
mutant() {
  m=${tmp}/$1.sh
  sed "$2" "${measure}" > "${m}"
  if ! grep -q -F -e "$3" "${measure}" || grep -q -F -e "$3" "${m}"; then
    echo "FAIL $1: the copy does not change ${3}"
    fail=1
    return
  fi
  keep=${fail} real=${measure}
  fail=0 measure=${m}
  cases > "${tmp}/$1.out"
  caught=${fail}
  fail=${keep} measure=${real}
  if [ "${caught}" = 1 ]; then
    echo "ok $1"
  else
    echo "FAIL $1: every case passed on the copy"
    fail=1
  fi
}
mutant no-issueCount 's/issueCount pageInfo/pageInfo/' 'issueCount pageInfo'
mutant no-headRefOid 's/{ url mergeable headRefOid }/{ url mergeable }/' \
  '{ url mergeable headRefOid }'
exit "${fail}"
