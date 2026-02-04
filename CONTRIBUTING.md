# Contributing to SupaBrain 🧠

Thanks for your interest in contributing! SupaBrain is built by and for the AI agent community.

## Ways to Contribute

- 🐛 **Report bugs** - Found something broken? Open an issue
- 💡 **Suggest features** - Have an idea? Let's discuss it
- 📝 **Improve docs** - Clarity helps everyone
- 🔧 **Submit PRs** - Code contributions welcome
- 🧪 **Test** - Try it with your agent and share feedback

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/supabrain.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit: `git commit -m "Add: your feature description"`
7. Push: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# Python environment
cd core
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database (local testing)
docker run --name supabrain-db -e POSTGRES_PASSWORD=dev -p 5432:5432 -d postgres:14
createdb -h localhost -U postgres supabrain
psql -h localhost -U postgres supabrain < schema.sql
```

## Code Style

- **Python:** Follow PEP 8, use `black` for formatting
- **JavaScript:** Use ES6+, Prettier for formatting
- **Commits:** Descriptive messages, reference issues when relevant

## Pull Request Guidelines

- Keep PRs focused (one feature/fix per PR)
- Include tests when adding features
- Update documentation as needed
- Link related issues
- Be patient and kind in reviews

## Community Guidelines

- Be respectful and constructive
- Assume good intent
- Help newcomers
- Share knowledge
- Have fun building cool stuff

## Questions?

- Open a [GitHub Discussion](https://github.com/Scarface86c/supabrain/discussions)
- Post on [Moltbook](https://moltbook.com)
- Tag `@Scar` on Moltbook for questions

---

Built with 🐺 for the agent community.
