# shellcheck shell=sh
# The measure of /btclib-inbox, which only reads. SKILL.md, beside this
# file, says what its output means. Run it as:
#
#   sh "${PROCESS:?}/skills/btclib-inbox/measure.sh" [--since <hours> | <time>]
#
# each query's output goes to "${d}/<name>.out", its stderr to
# "${d}/<name>.err" and its exit code to "${d}/<name>.rc"
d=$(mktemp -d "${TMPDIR:-/tmp}/btclib-inbox.XXXXXX") || exit 1
trap 'rm -r "${d}"' EXIT
trap 'exit 1' INT TERM
o=btclib-org
usage='usage: measure.sh [--since <hours> | <time> such as 2026-11-14T09:00:00Z],
the cutoff at most 720 hours (30 days) back and not ahead of now'
s=24
case $#:${1-} in
  0:) ;;
  2:--since) s=$2 ;;
  *) echo "${usage}"; exit 2 ;;
esac
at=$(jq -nr 'now | todate')
# the cutoff, or a jq error where it is not a time within the bound; a
# time or date must read back as written, as fromdate rolls 2026-11-00
# over to 2026-10-31
since=$(jq -nr --arg at "${at}" --arg s "${s}" '($at | fromdate) as $now
  | if $s | test("^[0-9]+$") then $now - ($s | tonumber) * 3600
    else ($s | if test("T") then . else . + "T00:00:00Z" end) as $t
      | ($t | fromdate) | if todate == $t then . else error("no such time")
        end end
  | if . >= $now - 720 * 3600 and . <= $now then todate
    else error("out of bounds") end' 2> /dev/null) || since=""
case ${since} in
  [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z) ;;
  *) echo "${usage}"; exit 2 ;;
esac
export d o since

cat > "${d}/run.sh" <<'EOF_RUN'
# run.sh <name> <command...>: the command's output, stderr and exit code
# into "${d}/<name>.out", "${d}/<name>.err" and "${d}/<name>.rc"
n=$1
shift
rc=0
"$@" > "${d}/${n}.out" 2> "${d}/${n}.err" || rc=$?
echo "${rc}" > "${d}/${n}.rc"
EOF_RUN

# check <name>...: "error: <name>: <its stderr>" and exit 1 where a
# command failed, printed anything on stderr, or did not run
check() {
  for n in "$@"; do
    if [ "$(cat "${d}/${n}.rc" 2> /dev/null)" != 0 ] || [ -s "${d}/${n}.err" ]
    then
      printf 'error: %s: %s\n' "${n}" \
        "$(tr '\n' ' ' < "${d}/${n}.err" 2> /dev/null)"
      exit 1
    fi
  done
}

# the open pull requests; 40 a page, as 100 a page fails now and then
# with HTTP 502
cat > "${d}/prs.graphql" <<'EOF_PRS'
query($q: String!, $endCursor: String) {
  search(query: $q, type: ISSUE, first: 40, after: $endCursor) {
    issueCount pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        number title url isDraft additions deletions changedFiles
        repository { name }
        author { __typename login }
        authorAssociation
        labels(first: 100) { pageInfo { hasNextPage } nodes { name } }
        reviewDecision mergeable headRefOid
        commits(last: 1) {
          nodes { commit { committedDate statusCheckRollup { state } } }
        }
        reviewRequests(first: 100) {
          pageInfo { hasNextPage }
          nodes { requestedReviewer { ... on User { login } } }
        }
        timelineItems(itemTypes: [REVIEW_REQUESTED_EVENT, LABELED_EVENT],
          last: 20) {
          nodes {
            ... on ReviewRequestedEvent {
              createdAt requestedReviewer { ... on User { login } }
            }
            ... on LabeledEvent { createdAt label { name } }
          }
        }
        reviews(last: 30) { nodes { author { __typename login } } }
        verdicts: reviews(author: "claude[bot]", last: 5) { nodes { body } }
        comments(last: 30) { nodes { author { __typename login } createdAt } }
      }
    }
  }
}
EOF_PRS

cat > "${d}/issues.graphql" <<'EOF_ISSUES'
query($q: String!, $endCursor: String) {
  search(query: $q, type: ISSUE, first: 100, after: $endCursor) {
    issueCount pageInfo { hasNextPage endCursor }
    nodes {
      ... on Issue {
        number title url createdAt
        repository { name }
        author { __typename login }
        authorAssociation
        labels(first: 100) { pageInfo { hasNextPage } nodes { name } }
        timelineItems(itemTypes: [LABELED_EVENT], last: 20) {
          nodes { ... on LabeledEvent { createdAt label { name } } }
        }
        comments(last: 30) { nodes { author { __typename login } createdAt } }
      }
    }
  }
}
EOF_ISSUES

# the open pull requests' review threads and CodeRabbit's reviews, in a
# search of their own that runs beside the other two
cat > "${d}/bots.graphql" <<'EOF_BOTS'
query($q: String!, $endCursor: String) {
  search(query: $q, type: ISSUE, first: 40, after: $endCursor) {
    issueCount pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        url
        reviewThreads(last: 100) {
          pageInfo { hasPreviousPage }
          nodes {
            isResolved opener: comments(first: 1) {
              nodes { author { __typename login } }
            }
            latest: comments(last: 1) {
              nodes { author { __typename login } createdAt }
            }
          }
        }
        coderabbit: reviews(author: "coderabbitai[bot]", last: 100) {
          pageInfo { hasPreviousPage } nodes { submittedAt body }
        }
      }
    }
  }
}
EOF_BOTS

# one issue or pull request, for "A person spoke on a closed item"
cat > "${d}/item.graphql" <<'EOF_ITEM'
query($o: String!, $r: String!, $n: Int!) {
  repository(owner: $o, name: $r) {
    issueOrPullRequest(number: $n) {
      ... on Issue { number title url state repository { name } }
      ... on PullRequest {
        number title url state additions deletions changedFiles
        repository { name }
      }
    }
  }
}
EOF_ITEM

# comments.sh <repo>: the repository's comments by a person created
# since ${since}, as "<repo>\t<n>\t<login>\t<time>"; the endpoint's since
# reads the time a comment was last updated
cat > "${d}/comments.sh" <<'EOF_COMMENTS'
r=$1
exec sh "${d}/run.sh" "comments.${r}" gh api --paginate \
  "repos/${o}/${r}/issues/comments?since=${since}&per_page=100" \
  --jq ".[] | select(.user.type == \"User\" and .created_at >= \"${since}\")
    | [\"${r}\", (.issue_url | split(\"/\") | last), .user.login,
       .created_at] | @tsv"
EOF_COMMENTS

# merge.sh <repo>/<n>: the pull request's URL, mergeability and head
cat > "${d}/merge.sh" <<'EOF_MERGE'
r=${1%/*} n=${1#*/}
exec sh "${d}/run.sh" "merge.${r}.${n}" gh api graphql -f o="${o}" \
  -f r="${r}" -F n="${n}" -f query='
  query($o: String!, $r: String!, $n: Int!) {
    repository(owner: $o, name: $r) {
      pullRequest(number: $n) { url mergeable headRefOid }
    }
  }' --jq '.data.repository.pullRequest
    | "\(.url)\t\(.mergeable)\t\(.headRefOid)"'
EOF_MERGE

# item.sh <repo>/<n>
cat > "${d}/item.sh" <<'EOF_ITEMSH'
r=${1%/*} n=${1#*/}
exec sh "${d}/run.sh" "item.${r}.${n}" gh api graphql -f o="${o}" \
  -f r="${r}" -F n="${n}" -F query=@"${d}/item.graphql" \
  --jq .data.repository.issueOrPullRequest
EOF_ITEMSH

# the items whose latest comment by a person since ${since} is not
# ${me}, and that the open searches did not return
cat > "${d}/spoke.jq" <<'EOF_SPOKE'
($open | map(.data.search.nodes[] | select(.url)
  | {("\(.repository.name)/\(.number)"): true}) | add // {}) as $seen
| [inputs | select(. != "") | split("\t")]
| group_by(.[0:2]) | map(max_by(.[3])) | .[]
| {k: "\(.[0])/\(.[1])", login: .[2], t: .[3]}
| select(.login != $me and ($seen[.k] | not))
EOF_SPOKE

# the list: each item in the first group that holds it, newest first
cat > "${d}/rows.jq" <<'EOF_ROWS'
def human: .author.__typename == "User";
def kind: if .url | contains("/pull/") then "PR" else "ISS" end;
def member: (.authorAssociation // "") | IN("OWNER", "MEMBER", "COLLABORATOR");
def held: [.labels.nodes[].name | select(IN("decision", "needs-maintainer"))]
  | first;
def labeled($l):
  [.timelineItems.nodes[] | select(.label.name? == $l) | .createdAt] | last;
def lastother: [.comments.nodes[] | select(human)] | last
  | if . != null and .author.login != $me then . else null end;
def asked: [.timelineItems.nodes[]
  | select(.requestedReviewer.login? == $me) | .createdAt] | last;
def green: .commits.nodes[0].commit.statusCheckRollup.state == "SUCCESS";
def unanswered: .author.login as $a
  | [.comments.nodes[], .reviews.nodes[]?
    | select(human and .author.login != $a)]
  | length == 0;
# the bot's verdict on the head, read as /btclib-pr's "The reviews on
# GitHub" reads it with gh pr view, but among the bot's latest reviews
# only: change both together
def ack: .headRefOid as $h
  | [.verdicts.nodes[] | ((.body // "") + "\n" | split("\n")[0])
    | select(test("^(ACK|CHANGES REQUESTED|NACK|NO VERDICT) " + $h + "(:|\\s|$)"))]
  | length > 0 and (last | startswith("ACK "));
def agentack: kind == "PR" and .author.login == "claude"
  and .author.__typename == "Bot" and (.isDraft | not) and green
  and (.reviewDecision // "REVIEW_REQUIRED") == "REVIEW_REQUIRED" and ack;
# a bot of /btclib-pr's "The reviews on GitHub"
def reviewbot: .__typename == "Bot"
  and (.login | IN("coderabbitai", "chatgpt-codex-connector", "claude"));
# each bot's thread and CodeRabbit review that waits on an answer, as
# SKILL.md's "Measure" says
def botwaits: .url as $u
  | ([$bots[].data.search.nodes[] | select(.url? == $u)] | first) as $b
  | ([.comments.nodes[] | select(.author.login == $me) | .createdAt]
    | last) as $mine
  | [($b.reviewThreads.nodes[]? | select(.isResolved | not)
      | .opener.nodes[0].author as $o
      | select(($o | reviewbot) and .latest.nodes[0].author == $o)
      | {login: $o.login, t: .latest.nodes[0].createdAt, review: false}),
    ($b.coderabbit.nodes[]? | select((.body // "") | test("\\S"))
      | select($mine == null or .submittedAt > $mine)
      | {login: "coderabbitai", t: .submittedAt, review: true})];
def botline: group_by(.login) | map(.[0].login + " "
    + ([(map(select(.review | not)) | length | select(. > 0)
        | "\(.) thread" + (if . == 1 then "" else "s" end)),
      (map(select(.review)) | length | select(. > 0)
        | "\(.) review" + (if . == 1 then "" else "s" end))] | join(" and ")))
  | join(", ");
def age: if . == null then "?" else
  [0, ($at | fromdate) - fromdate] | max / 3600 | floor
  | if . < 48 then "\(.) h" else "\(. / 24 | floor) d" end end;
def balance: if kind == "PR" then " \(.changedFiles) file"
  + (if .changedFiles == 1 then "" else "s" end)
  + ", +\(.additions)/-\(.deletions)" else "" end;
def link: "[\(kind) \(.repository.name)#\(.number)](\(.url))";
def row($g; $t; $why; $mark): {g: $g, t: $t,
  slug: "\(.repository.name)/\(.number)", link: link, line: ("- \($t | age) "
  + "\(link)\(balance) — \($why)"
  + (if $mark and ($t // "") >= $since then " (new)" else "" end)
  + " — \(.title[:50] | gsub("[[:cntrl:]]"; " ")
    | gsub("(?<c>[\\\\`*_\\[\\]<>#|~&])"; "\\\(.c)"))")};
[ ($open | map(.data.search.nodes[] | select(.url)) | unique_by(.url) | .[]
    | if (held | not) and lastother then
        row(1; lastother.createdAt; "\(lastother.author.login) spoke last"; true)
      elif kind == "PR" and (held | not) and human and (member | not)
          and (.isDraft | not) and green and unanswered then
        row(1; .commits.nodes[0].commit.committedDate;
          "\(.author.login)'s, green, no reply"; true)
      elif kind == "ISS" and (held | not) and human and (member | not)
          and unanswered then
        row(1; .createdAt; "\(.author.login)'s, no reply"; true)
      elif held then row(2; labeled(held); held; true)
      elif kind == "PR"
          and any(.reviewRequests.nodes[]; .requestedReviewer.login? == $me)
        then row(3; asked; "your review"; true)
      elif agentack and .mergeable == "MERGEABLE" then
        row(4; .commits.nodes[0].commit.committedDate;
          "ACK, needs your approval"; true)
      # group 4's but for a mergeability GitHub has not computed yet:
      # named on the last line, not left out unsaid
      elif agentack and .mergeable == "UNKNOWN" then row(0; null; ""; false)
      # aged from the longest wait, so that a new finding hides no old one
      elif botwaits | length > 0 then
        botwaits as $w | row(5; $w | map(.t) | min; $w | botline; true)
      else empty end),
  (($spoke | map({(.k): .}) | add // {}) as $s
    | $closed[] | select(. != null and .state != "OPEN")
    | $s["\(.repository.name)/\(.number)"] as $c
    | row(6; $c.t; "\($c.login) spoke last"; false)) ]
# the groups, then one line holding a JSON array of those of unknown
# mergeability
| (map(select(.g > 0)) | group_by(.g) | .[]
    | ["A person waits on an answer", "Asked of you", "Your review requested",
       "The bot's ACK, needs your approval", "A bot waits on an answer",
       "A person spoke on a closed item"][.[0].g - 1] as $h
    | "**\($h)**", "", (sort_by(.t) | reverse | .[].line), ""),
  (map(select(.g == 0) | {slug, link}) | sort_by(.slug) | tojson)
EOF_ROWS

sh "${d}/run.sh" me gh api user --jq .login
check me
me=$(cat "${d}/me.out")
sh "${d}/run.sh" repos gh repo list "${o}" --no-archived --limit 200 \
  --json name --jq '.[].name'
check repos
sh "${d}/run.sh" prs gh api graphql --paginate -f q="org:${o} is:open is:pr" \
  -F query=@"${d}/prs.graphql" &
sh "${d}/run.sh" issues gh api graphql --paginate \
  -f q="org:${o} is:open is:issue" -F query=@"${d}/issues.graphql" &
sh "${d}/run.sh" bots gh api graphql --paginate -f q="org:${o} is:open is:pr" \
  -F query=@"${d}/bots.graphql" &
# GNU xargs runs its command once on empty input; BSD xargs does not
[ ! -s "${d}/repos.out" ] ||
  xargs -n 1 -P 6 sh "${d}/comments.sh" < "${d}/repos.out" &
wait
check prs issues bots
# a search with no count of matches, or cut short at GitHub's cap on
# results, as SKILL.md says
for n in prs issues bots; do
  short=$(jq -nr '[inputs | .data.search]
    | if length == 0 or any(.[]; .issueCount == null) then
        "the search gave no count of matches"
      else ([.[].issueCount] | max) as $c
        | ([.[].nodes[] | .url // empty] | unique | length) as $r
        | if $c > $r then
            "the search was cut short: \($c) matches, \($r) returned"
          else empty end end' "${d}/${n}.out") || exit 1
  if [ -n "${short}" ]; then
    printf 'error: %s: %s\n' "${n}" "${short}"
    exit 1
  fi
done
# review threads and CodeRabbit's reviews are read 100 at a time, and
# never cut short
more=$(jq -r '.data.search.nodes[]
    | select(.reviewThreads.pageInfo.hasPreviousPage
      or .coderabbit.pageInfo.hasPreviousPage) | .url' "${d}/bots.out") ||
  exit 1
if [ -n "${more}" ]; then
  printf 'error: over 100 review threads or CodeRabbit reviews: %s\n' \
    "$(printf '%s' "${more}" | tr '\n' ' ')"
  exit 1
fi
while read -r r; do
  check "comments.${r}"
done < "${d}/repos.out"
cat "${d}/prs.out" "${d}/issues.out" > "${d}/open.json"
# labels and review requests are read 100 at a time, and never cut short
more=$(jq -r '.data.search.nodes[] | select(.labels.pageInfo.hasNextPage
    or .reviewRequests.pageInfo.hasNextPage) | .url' "${d}/open.json") ||
  exit 1
if [ -n "${more}" ]; then
  printf 'error: over 100 labels or review requests: %s\n' \
    "$(printf '%s' "${more}" | tr '\n' ' ')"
  exit 1
fi
while read -r r; do
  cat "${d}/comments.${r}.out"
done < "${d}/repos.out" |
  jq -nRc --arg me "${me}" --slurpfile open "${d}/open.json" \
    -f "${d}/spoke.jq" > "${d}/spoke.json" || exit 1
jq -r .k "${d}/spoke.json" > "${d}/spoke.keys" || exit 1
[ ! -s "${d}/spoke.keys" ] ||
  xargs -n 1 -P 6 sh "${d}/item.sh" < "${d}/spoke.keys"
while read -r k; do
  check "item.${k%/*}.${k#*/}"
done < "${d}/spoke.keys"
while read -r k; do
  cat "${d}/item.${k%/*}.${k#*/}.out"
done < "${d}/spoke.keys" > "${d}/closed.json"
rows() {
  jq -nr --arg me "${me}" --arg since "${since}" --arg at "${at}" \
    --slurpfile open "${d}/open.json" --slurpfile spoke "${d}/spoke.json" \
    --slurpfile closed "${d}/closed.json" --slurpfile bots "${d}/bots.out" \
    -f "${d}/rows.jq" \
    > "${d}/rows.md" || exit 1
  tail -n 1 "${d}/rows.md" > "${d}/unknown.json"
  jq -r '.[].slug' "${d}/unknown.json" > "${d}/unknown.keys" || exit 1
}
rows
# GitHub computes a pull request's mergeability once it is asked for:
# those still unknown are read once more, 5 s later, and no more. One
# whose head moved in between keeps its unknown mergeability, since its
# verdict and checks were read on the earlier head
if [ -s "${d}/unknown.keys" ]; then
  sleep 5
  xargs -n 1 -P 6 sh "${d}/merge.sh" < "${d}/unknown.keys"
  while read -r k; do
    check "merge.${k%/*}.${k#*/}"
  done < "${d}/unknown.keys"
  while read -r k; do
    cat "${d}/merge.${k%/*}.${k#*/}.out"
  done < "${d}/unknown.keys" > "${d}/merge.tsv"
  jq -c --rawfile m "${d}/merge.tsv" '([$m | split("\n")[] | select(. != "")
      | split("\t") | {(.[0]): {mergeable: .[1], head: .[2]}}] | add) as $m
    | .data.search.nodes |= map($m[.url // ""] as $r
      | if $r != null and $r.head == .headRefOid
        then .mergeable = $r.mergeable else . end)' \
    "${d}/open.json" > "${d}/open2.json" || exit 1
  mv "${d}/open2.json" "${d}/open.json"
  rows
fi
sed '$d' "${d}/rows.md"
u=$(jq -r 'map(.link) | join(", ")' "${d}/unknown.json") || exit 1
echo "since ${since}, read at ${at}${u:+; mergeability unknown: ${u}}"
