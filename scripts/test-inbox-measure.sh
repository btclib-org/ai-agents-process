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
# query asks for it. A string `@since@` or `@since-<s>@` in an answer is
# served as the time measure.sh exports in ${since}, or <s> seconds
# before it. A stand-in for sleep returns at once. Each case has
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
# - claimed: the maintainer's claims stand on four outside persons'
#   issues, the first an hour old, the others older than a day. The
#   second has another person's comment before its claim, the fourth its
#   author's after it. The agent's pull request closes the first issue,
#   and a second one of the agent closes the third, its head committed
#   after that issue's claim. Exits 0, with each issue in group 1, only
#   the second as `claim idle`, and each pull request showing its
#   issue's claim.
# - released: the maintainer's claim on the issue is followed by a
#   release. Exits 0, with the issue in group 1 and no claim.
# - closed: a person spoke last on two closed pull requests that carry
#   the maintainer's claim, one of them merged; on two closed issues the
#   maintainer wrote after a person, a release on one and an answer on
#   the other. Exits 0, with both pull requests and the released issue
#   in the last group, and the claim on the pull request not merged.
# - edges: the maintainer's claims on outside persons' issues are 24
#   hours old to the second, and one second more; another member's
#   claim follows an outside person's issue; the agent's pull request
#   closes two claimed issues, the claim on the second the later. Exits
#   0, with the older of the two 24-hour claims as `claim idle` and the
#   other not, the member's claim an answer, and the pull request
#   showing the later claim.
#
# Then the cases run again on copies of measure.sh, each with one field
# taken out of its queries: `issueCount` from both searches, `headRefOid`
# from the second read of a mergeability, a comment's `body` from the
# issue search and from the read of a closed item, and
# `closingIssuesReferences` from the pull request search. A copy is
# caught, and prints `ok`, where some case fails on it.
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
  graphql::*"issueOrPullRequest(number"*) file=item.${r}.${n}.json ;;
  *) echo "gh stand-in: no answer for: $*" >&2; exit 1 ;;
esac
if [ "${what}" = graphql ]; then
  jq -c --arg q "${query}" '[$q | scan("[A-Za-z_][A-Za-z0-9_]*")] as $w
    | .data |= walk(if type == "object" then
        with_entries(select(.key as $k | any($w[]; . == $k))) else . end)' \
    "${FIX:?}/${file}"
else
  cat "${FIX:?}/${file}"
fi | jq -c --arg s "${since:?}" 'walk(if type == "string"
    and test("^@since(-[0-9]+)?@$")
  then ($s | fromdate) + (.[6:-1] | if . == "" then 0 else tonumber end)
    | todate else . end)' |
  if [ -n "${f}" ]; then jq -r "${f}"; else cat; fi
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
# issue [<n> <login>]: an outside person's issue with no reply, as the
# search returns it, 3 by alice where none is given
issue() {
  jq -nc --argjson n "${1:-3}" --arg l "${2:-alice}" --arg u "${u}" '{
    number: $n, title: "Issue \($n)", url: "\($u)/issues/\($n)",
    createdAt: "2026-01-01T00:00:00Z", repository: {name: "repo-a"},
    author: {__typename: "User", login: $l}, authorAssociation: "NONE",
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
# comment <login> <time> <body>: a person's comment
comment() {
  jq -nc --arg l "$1" --arg t "$2" --arg b "$3" \
    '{author: {__typename: "User", login: $l}, createdAt: $t, body: $b}'
}
# said <comment>...: the item on stdin, with these comments
said() {
  jq -c --argjson c "$(printf '%s\n' "$@" | jq -sc .)" '.comments.nodes = $c'
}
# closes <n>...: the pull request on stdin, its closing references naming
# these issues
closes() {
  jq -c --argjson c "$(printf '%s\n' "$@" | jq -sc .)" --arg u "${u}" \
    '.closingIssuesReferences = {pageInfo: {hasNextPage: false},
      nodes: ($c | map({url: "\($u)/issues/\(.)"}))}'
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
hour=$(jq -nr 'now - 3600 | todate')
two=$(jq -nr 'now - 7200 | todate')
claim="Claimed: a session is taking this."
new claimed
page 4 false "$(issue | said "$(comment maintainer "${hour}" "${claim}")")" \
  "$(issue 4 carol | said "$(comment bob 2026-01-03T00:00:00Z "A question.")" \
    "$(comment maintainer 2026-01-04T00:00:00Z "${claim}")")" \
  "$(issue 5 dave |
    said "$(comment maintainer 2026-01-04T00:00:00Z "${claim}")")" \
  "$(issue 6 erin |
    said "$(comment maintainer 2026-01-04T00:00:00Z "${claim}")" \
      "$(comment erin 2026-01-05T00:00:00Z "Any news?")")" \
  > "${tmp}/claimed/issues.json"
page 2 false "$(pr 7 "${a}" MERGEABLE | closes 3)" \
  "$(pr 8 "${a}" MERGEABLE | closes 5 |
    jq -c '.commits.nodes[0].commit.committedDate = "2026-01-05T00:00:00Z"')" \
  > "${tmp}/claimed/prs.json"
new released
page 1 false "$(issue |
  said "$(comment maintainer 2026-01-03T00:00:00Z "${claim}")" \
    "$(comment maintainer 2026-01-04T00:00:00Z "Released: it ended.")")" \
  > "${tmp}/released/issues.json"
new closed
jq -nc --arg h "${hour}" --arg t "${two}" '[(9, 10 | [., "alice", $h, "Hi"]),
  (11, 12 | [., "alice", $t, "A question."]),
  [11, "maintainer", $h, "Released: it landed."], [12, "maintainer", $h, "Done."]
  | {user: {type: "User", login: .[1]}, created_at: .[2], body: .[3],
    issue_url: "https://api.github.com/repos/btclib-org/repo-a/issues/\(.[0])"}]' \
  > "${tmp}/closed/comments.json"
for n in 11 12; do
  issue "${n}" alice |
    jq -c '{data: {repository: {issueOrPullRequest: (.state = "CLOSED")}}}' \
    > "${tmp}/closed/item.repo-a.${n}.json"
done
for x in 9:CLOSED 10:MERGED; do
  pr "${x%:*}" "${a}" MERGEABLE |
    said "$(comment maintainer "${two}" "${claim}")" \
      "$(comment alice "${hour}" "Still there?")" |
    jq -c --arg s "${x#*:}" '{data: {repository:
      {issueOrPullRequest: (.state = $s)}}}' \
    > "${tmp}/closed/item.repo-a.${x%:*}.json"
done
new edges
page 5 false "$(issue 7 frank | said "$(comment maintainer @since@ "${claim}")")" \
  "$(issue 8 gina | said "$(comment maintainer @since-1@ "${claim}")")" \
  "$(issue 10 henk | said "$(comment bob "${hour}" "${claim}")")" \
  "$(issue 11 ivan |
    said "$(comment maintainer 2026-01-04T00:00:00Z "${claim}")")" \
  "$(issue 12 judy | said "$(comment maintainer "${hour}" "${claim}")")" \
  > "${tmp}/edges/issues.json"
page 1 false "$(pr 7 "${a}" MERGEABLE | closes 11 12)" \
  > "${tmp}/edges/prs.json"

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

# row <n> [<claim>]: a row of group 4 after its age, which is counted
# from now
iss="[ISS repo-a#3](${u}/issues/3) — alice's, no reply — Issue 3"
row() {
  echo "[PR repo-a#$1](${u}/pull/$1) 1 file, +2/-1 — ACK, needs your" \
    "approval${2:+ — $2} — Pull $1"
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
  by="claimed by maintainer"
  run claimed 0 "${iss% — Issue 3} — ${by}, 1 h — Issue 3" \
    "[ISS repo-a#4](${u}/issues/4) — bob spoke last — ${by}, claim idle " \
    "[ISS repo-a#5](${u}/issues/5) — dave's, no reply — ${by}, " \
    "[ISS repo-a#6](${u}/issues/6) — erin spoke last — ${by}, " \
    "$(row 7 "${by}, 1 h")" \
    "[PR repo-a#8](${u}/pull/8) 1 file, +2/-1 — ACK, needs your approval — ${by}, " \
    -- "no reply — ${by}, claim idle" "approval — ${by}, claim idle" \
    "erin spoke last — ${by}, claim idle" "error:"
  run released 0 "${iss}" -- "claimed by" "error:"
  run closed 0 "**A person spoke on a closed item**" \
    "[PR repo-a#9](${u}/pull/9) 1 file, +2/-1 — alice spoke last — ${by}, 2 h — Pull 9" \
    "[PR repo-a#10](${u}/pull/10) 1 file, +2/-1 — alice spoke last — Pull 10" \
    "[ISS repo-a#11](${u}/issues/11) — alice spoke last — Issue 11" \
    -- "[ISS repo-a#12]" "error:"
  run edges 0 "[ISS repo-a#7](${u}/issues/7) — frank's, no reply — ${by}, 24 h" \
    "[ISS repo-a#8](${u}/issues/8) — gina's, no reply — ${by}, claim idle 24 h" \
    "[ISS repo-a#10](${u}/issues/10) — bob spoke last (new) — claimed by bob, 1 h" \
    "$(row 7 "${by}, 1 h")" -- "error:"
}
cases

# mutant <name> <sed script> <text it changes>: the cases on a copy of
# measure.sh the sed script changed, caught where a case fails; the copy
# holds the text on fewer lines than measure.sh
mutant() {
  m=${tmp}/$1.sh
  sed "$2" "${measure}" > "${m}"
  if [ "$(grep -c -F -e "$3" "${m}")" -ge \
    "$(grep -c -F -e "$3" "${measure}")" ]; then
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
mutant no-issues-body \
  '/<<.EOF_ISSUES.$/,/^EOF_ISSUES$/s/createdAt body/createdAt/' 'createdAt body'
mutant no-closingIssuesReferences \
  '/<<.EOF_PRS.$/,/^EOF_PRS$/{/closingIssuesReferences/{N;N;d;};}' \
  'closingIssuesReferences(first: 100) {'
mutant no-item-body \
  '/<<.EOF_ITEM.$/,/^EOF_ITEM$/s/createdAt body/createdAt/' 'createdAt body'
exit "${fail}"
