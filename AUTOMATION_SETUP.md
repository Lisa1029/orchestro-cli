# Orchestro Automation Setup Guide

**Status**: ✅ Automation Implemented
**Last Updated**: 2025-11-17

---

## 🎉 What's Been Automated

We've implemented a complete automation system for Orchestro that handles:

✅ **Release Management** - Auto-changelog, GitHub releases, PyPI publishing
✅ **Community Engagement** - Auto-reply to issues, thank contributors
✅ **Analytics** - Weekly stats reports
✅ **Issue Management** - Auto-labeling based on content

---

## 📦 GitHub Actions (Already Active)

### Workflows Implemented

1. **`.github/workflows/release.yml`** - Automated Releases
   - Triggers on: Git tags (v*)
   - Actions:
     - Generate changelog from commits
     - Create GitHub release
     - Post to Discord (if configured)
     - Publish to PyPI (if configured)

2. **`.github/workflows/auto-reply.yml`** - Issue Auto-Responder
   - Triggers on: New issues
   - Actions:
     - Detect issue type (bug, feature, question, install)
     - Send helpful auto-reply
     - Add appropriate labels

3. **`.github/workflows/weekly-stats.yml`** - Weekly Reports
   - Triggers on: Every Monday 9am UTC (or manual)
   - Actions:
     - Collect GitHub stats (stars, forks, issues, PRs)
     - Fetch PyPI download stats
     - Post to Discord (if configured)
     - Create summary report

4. **`.github/workflows/thank-contributor.yml`** - Thank Contributors
   - Triggers on: Merged PRs
   - Actions:
     - Thank contributor publicly
     - Suggest next steps
     - Link to community resources

5. **`.github/workflows/auto-label.yml`** - Auto-Label Issues/PRs
   - Triggers on: New issues or PRs
   - Actions:
     - Analyze title and body
     - Add relevant labels (bug, enhancement, docs, etc.)
     - Categorize by component (api, parallel, cli, etc.)

---

## 🔧 Setup Required

### 1. GitHub Secrets (Optional but Recommended)

Go to: **Settings → Secrets and variables → Actions**

Add these secrets:

```
DISCORD_WEBHOOK
- Get from Discord: Server Settings → Integrations → Webhooks → New Webhook
- Format: https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN

PYPI_API_TOKEN
- Get from: https://pypi.org/manage/account/token/
- Create token with "Upload packages" permission
- Format: pypi-AgEIcHlwaS5vcmc... (starts with pypi-)

OPENAI_API_KEY (future use - for AI content generation)
- Get from: https://platform.openai.com/api-keys
- Format: sk-...
```

### 2. GitHub Variables (Optional)

Go to: **Settings → Secrets and variables → Actions → Variables**

Add these variables:

```
DISCORD_WEBHOOK
- Same as secret, but as variable for conditional checks
```

### 3. Labels Setup

Create these labels in your repo:
- `bug` - 🐛 Bug reports
- `enhancement` - ✨ Feature requests
- `documentation` - 📚 Documentation
- `good first issue` - 👋 Good for newcomers
- `question` - ❓ Questions
- `api` - 🌐 API related
- `parallel` - ⚡ Parallel execution
- `scheduler` - 📅 Scheduler related
- `intelligence` - 🧠 Intelligence system
- `cli` - 💻 CLI related
- `testing` - 🧪 Testing related
- `security` - 🔒 Security
- `performance` - 🚀 Performance

---

## 🚀 Testing the Automation

### Test 1: Issue Auto-Reply

1. Create a test issue with title: "Bug: Test automation"
2. Body: "This is a test bug report"
3. Watch for:
   - Auto-reply comment within seconds
   - `bug` label automatically added

### Test 2: Weekly Stats (Manual Trigger)

1. Go to: Actions → Weekly Stats Report
2. Click: Run workflow
3. Watch for:
   - Stats collection
   - Discord post (if configured)
   - Job summary

### Test 3: Release Automation (When Ready)

```bash
# Create and push a tag
git tag v0.2.2
git push --tags

# Watch for:
# - Changelog generation
# - GitHub release creation
# - Discord notification
# - PyPI publish (if token configured)
```

---

## 🛠️ n8n Setup (Advanced Automation)

### Quick Start with Docker

```bash
# Start n8n
docker-compose -f docker-compose.n8n.yml up -d

# Access n8n
open http://localhost:5678

# Login with:
# Username: admin
# Password: change_this_password (update in docker-compose.n8n.yml first!)
```

### Initial Configuration

1. **Change Password**:
   - Edit `docker-compose.n8n.yml`
   - Change `N8N_BASIC_AUTH_PASSWORD`
   - Restart: `docker-compose -f docker-compose.n8n.yml restart`

2. **Set Timezone**:
   - Edit `GENERIC_TIMEZONE` to your timezone
   - Example: `America/New_York`, `Europe/London`, `Asia/Tokyo`

3. **Access n8n**:
   - Open: http://localhost:5678
   - Login with credentials from docker-compose file

### Sample Workflows (Create in n8n)

#### Workflow 1: Blog to Social Media

```
1. Add Webhook node
   - Method: POST
   - Path: blog-post
   - Authentication: None (or basic auth)

2. Add HTTP Request node
   - Method: GET
   - URL: {{ $json.blog_url }}
   - Extract blog content

3. Add OpenAI node (if API key available)
   - Model: gpt-4
   - Prompt: "Convert this blog post to a tweet thread (7 tweets max):\n\n{{ $json.content }}"

4. Add multiple output nodes:
   - Save to Google Sheets (content calendar)
   - Post to Twitter (if API configured)
   - Send to Discord webhook
```

#### Workflow 2: Daily Stats Aggregation

```
1. Schedule Trigger node
   - Trigger Interval: Daily
   - Trigger at: 00:00 (midnight)

2. HTTP Request node (GitHub)
   - URL: https://api.github.com/repos/vyb/orchestro-cli
   - Authentication: Bearer token (GitHub PAT)

3. HTTP Request node (PyPI)
   - URL: https://pypistats.org/api/packages/orchestro-cli/recent

4. Aggregate node
   - Combine data from both sources

5. Google Sheets node
   - Operation: Append
   - Sheet: "Daily Stats"
```

---

## 📊 Monitoring

### Check Automation Status

1. **GitHub Actions**:
   - Go to: Actions tab in your repo
   - See all workflow runs
   - Check for failures

2. **n8n**:
   - Dashboard: http://localhost:5678
   - Executions tab shows all workflow runs
   - View logs and debug

### Troubleshooting

**Issue**: Release workflow fails
- Check if `GITHUB_TOKEN` has correct permissions
- Verify tag format (must start with `v`)

**Issue**: Discord webhook not working
- Verify webhook URL is correct
- Test with: `curl -X POST -H "Content-Type: application/json" -d '{"content":"Test"}' YOUR_WEBHOOK_URL`

**Issue**: PyPI publish fails
- Verify API token is correct
- Check package version isn't already published
- Ensure `pyproject.toml` version matches tag

**Issue**: n8n won't start
- Check if port 5678 is available
- View logs: `docker-compose -f docker-compose.n8n.yml logs n8n`
- Ensure Docker has enough resources

---

## 🎯 Next Steps

### Week 1: Test & Verify
- [x] Test issue auto-reply
- [x] Test weekly stats (manual)
- [ ] Configure Discord webhook
- [ ] Configure PyPI token
- [ ] Test release workflow

### Week 2: n8n Setup
- [ ] Start n8n with Docker
- [ ] Create first workflow (blog → social)
- [ ] Create stats aggregation workflow
- [ ] Test webhooks

### Week 3: Content Automation
- [ ] Set up social media accounts (Twitter, LinkedIn)
- [ ] Configure Postiz or Buffer
- [ ] Create content calendar
- [ ] Schedule first week of posts

### Week 4: Optimization
- [ ] Review automation performance
- [ ] Adjust workflows based on results
- [ ] Add more automations
- [ ] Document learnings

---

## 📚 Resources

### GitHub Actions
- [Documentation](https://docs.github.com/en/actions)
- [Workflow syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Marketplace](https://github.com/marketplace?type=actions)

### n8n
- [Documentation](https://docs.n8n.io)
- [Node documentation](https://docs.n8n.io/integrations/)
- [Community workflows](https://n8n.io/workflows)
- [Forum](https://community.n8n.io)

### Docker
- [Docker Compose docs](https://docs.docker.com/compose/)
- [n8n Docker setup](https://docs.n8n.io/hosting/installation/docker/)

---

## 🎉 Success Metrics

Track these weekly:

- ✅ Issues auto-replied: X/week
- ✅ PRs auto-thanked: X/week
- ✅ Release automated: Yes/No
- ✅ Stats reports sent: X/week
- ✅ Time saved: X hours/week

**Goal**: 80% of routine tasks automated within 4 weeks

---

## 💡 Pro Tips

1. **Start Small**: Enable one workflow at a time
2. **Test First**: Use manual triggers before automating
3. **Monitor Closely**: Check Actions tab daily for first week
4. **Iterate**: Adjust auto-reply templates based on feedback
5. **Document**: Keep notes on what works/doesn't

---

**Status**: All GitHub Actions are live and ready to use!

**Next**: Configure secrets and test the workflows.

🚀 **Automation is now active!**
