#!/usr/bin/env python3
"""
NightShift Task Router - Routes whitelisted tasks to appropriate handlers

Allowed task types:
- repo_sync: Git operations (pull, push, sync)
- squirt_batch: Batch document generation
- sherlock_export: Topic-based evidence extraction
- lint: Code formatting
- backup: Safe backup operations
- llm_job: Route to J5AWorker for LLM-based processing
"""
import os, sys, json, subprocess, shlex, pathlib
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "nightshift"
ALLOWED = {"repo_sync", "squirt_batch", "sherlock_export", "sherlock_content_collection", "sherlock_research_execution", "lint", "backup", "llm_job"}

def run(cmd, cwd=None):
    """Execute command safely"""
    print(f"$ {cmd}")
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True, cwd=cwd)
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)
    else:
        print(p.stdout[:4000])
    return p.returncode == 0

def handle_repo_sync(args):
    """Handle git repository sync operations"""
    manifest = args.get("manifest", str(ROOT / "configs" / "repos.json"))

    with open(manifest) as f:
        repos = json.load(f)

    results = []
    for repo in repos:
        name = repo["name"]
        path = repo["path"]
        branch = repo.get("branch", "main")

        print(f"\n=== Syncing {name} ===")

        # Check if repo exists
        if not pathlib.Path(path).exists():
            print(f"⚠️  Repository path does not exist: {path}")
            results.append({"repo": name, "status": "missing"})
            continue

        # Pull latest changes
        if run(f"cd {shlex.quote(path)} && git pull origin {shlex.quote(branch)}", cwd=path):
            results.append({"repo": name, "status": "synced"})
        else:
            results.append({"repo": name, "status": "failed"})

    return {"results": results}

def handle_squirt_batch(args):
    """Handle batch document generation through Squirt"""
    batch_csv = args.get("batch_file")
    output_dir = args.get("output", str(ART / datetime.now().strftime("%Y-%m-%d") / "squirt"))

    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    squirt_cli = ROOT / "integrations" / "squirt_cli.py"
    cmd = f"python3 {shlex.quote(str(squirt_cli))} --batch {shlex.quote(batch_csv)} --out {shlex.quote(output_dir)}"

    if run(cmd):
        return {"status": "completed", "output_dir": output_dir}
    else:
        return {"status": "failed"}

def handle_sherlock_export(args):
    """Handle topic-based evidence extraction from Sherlock"""
    topic = args.get("topic")
    output_file = args.get("out")

    if not output_file:
        output_file = str(ART / datetime.now().strftime("%Y-%m-%d") / "sherlock" / f"{topic.replace(' ', '_')}_packet.jsonl")

    pathlib.Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    sherlock_export = ROOT / "integrations" / "sherlock_export_topic.py"
    sherlock_root = args.get("sherlock_path", "/home/johnny5/Sherlock")

    # Change to Sherlock directory for export
    cmd = f"cd {shlex.quote(sherlock_root)} && python3 {shlex.quote(str(sherlock_export))} --topic {shlex.quote(topic)} --out {shlex.quote(output_file)}"

    if run(cmd):
        return {"status": "completed", "output": output_file}
    else:
        return {"status": "failed"}

def handle_lint(args):
    """Handle code formatting and linting"""
    target = args.get("target", str(ROOT))
    fix = args.get("fix", True)

    results = {}

    # Run black formatter if fix=True
    if fix:
        if run(f"black {shlex.quote(target)}"):
            results["black"] = "applied"
        else:
            results["black"] = "failed"
    else:
        if run(f"black --check {shlex.quote(target)}"):
            results["black"] = "passed"
        else:
            results["black"] = "would_reformat"

    # Try ruff if available
    if run(f"ruff check --fix {shlex.quote(target)} || true"):
        results["ruff"] = "checked"

    return results

def handle_backup(args):
    """Handle safe backup operations"""
    source = args.get("source")
    dest = args.get("dest", str(ART / datetime.now().strftime("%Y-%m-%d") / "backups"))

    pathlib.Path(dest).mkdir(parents=True, exist_ok=True)

    # Use rsync for safe backups
    cmd = f"rsync -av --progress {shlex.quote(source)} {shlex.quote(dest)}"

    if run(cmd):
        return {"status": "completed", "dest": dest}
    else:
        return {"status": "failed"}

def handle_llm_job(args):
    """Route LLM-based job to J5AWorker"""
    # Convert to nightshift job format and write to queue
    job_file = ROOT / "j5a-nightshift" / "ops" / "queue" / "nightshift_jobs.json"

    # Load existing jobs or create new list
    if job_file.exists():
        with open(job_file) as f:
            jobs = json.load(f)
    else:
        jobs = []

    # Add new job
    jobs.append(args.get("job_spec"))

    # Write back
    with open(job_file, 'w') as f:
        json.dump(jobs, f, indent=2)

    print(f"✅ LLM job queued in {job_file}")
    return {"status": "queued", "queue": str(job_file)}

def handle_sherlock_content_collection(args):
    """
    Handle Sherlock content collection (deterministic scraping/downloading)

    This is a lightweight handler that collects raw content without analysis.
    For full research execution with Claude analysis, use sherlock_research_execution.
    """
    package_id = args.get("package_id")
    target_name = args.get("target_name")
    package_type = args.get("package_type")
    collection_urls = args.get("collection_urls", [])

    print(f"\n📚 Sherlock Content Collection: {target_name}")
    print(f"   Package ID: {package_id}")
    print(f"   Type: {package_type}")
    print(f"   URLs: {len(collection_urls)}")

    # Create output directory
    output_dir = ART / datetime.now().strftime("%Y-%m-%d") / "sherlock" / "content"
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = target_name.lower().replace(' ', '_').replace('—', '-')[:50]

    # Collect content (basic web scraping)
    collected = []
    for i, url in enumerate(collection_urls, 1):
        print(f"\n   [{i}/{len(collection_urls)}] Collecting: {url[:60]}...")

        try:
            # Use curl for basic content collection
            output_file = output_dir / f"{safe_name}_{i}.html"
            cmd = f"curl -L -s --max-time 30 {shlex.quote(url)} -o {shlex.quote(str(output_file))}"

            if run(cmd):
                collected.append(str(output_file))
                print(f"       ✅ Saved to: {output_file.name}")
            else:
                print(f"       ⚠️  Failed to collect")

        except Exception as e:
            print(f"       ❌ Error: {e}")
            continue

    # Create manifest file
    manifest = {
        "package_id": package_id,
        "target_name": target_name,
        "package_type": package_type,
        "collected_files": collected,
        "collection_urls": collection_urls,
        "collected_at": datetime.now().isoformat(),
        "collected_count": len(collected),
        "requested_count": len(collection_urls)
    }

    manifest_file = output_dir / f"{safe_name}_manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n   ✅ Collected {len(collected)}/{len(collection_urls)} sources")
    print(f"   📄 Manifest: {manifest_file}")

    # Update package status in Sherlock database
    try:
        sys.path.append('/home/johnny5/Johny5Alive/integrations')
        from sherlock_status_updater import update_package_status
        update_package_status(package_id, 'running', {
            'stage': 'content_collection',
            'collected_count': len(collected)
        })
    except Exception as e:
        print(f"   ⚠️  Status update failed: {e}")

    return {
        "status": "completed",
        "collected_count": len(collected),
        "manifest": str(manifest_file),
        "output_dir": str(output_dir)
    }

def handle_sherlock_research_execution(args):
    """
    Execute full Sherlock research package with Claude analysis

    This handler performs the complete research pipeline:
    1. Content collection (if not already done)
    2. Claim extraction via Claude API
    3. Entity recognition
    4. Evidence card generation
    5. Database storage
    """
    package_id = args.get("package_id")
    target_name = args.get("target_name")

    print(f"\n🔬 Sherlock Research Execution: {target_name}")
    print(f"   Package ID: {package_id}")

    # Import and execute research executor
    sys.path.append(str(ROOT / 'src'))

    try:
        from sherlock_research_executor import SherlockResearchExecutor

        executor = SherlockResearchExecutor()

        # Execute research package
        result = executor.execute_package(args)

        print(f"\n   {'✅' if result.success else '❌'} Research {'completed' if result.success else 'failed'}")
        print(f"   Claims extracted: {result.claims_extracted}")
        print(f"   Entities found: {result.entities_found}")
        print(f"   Outputs: {len(result.outputs_generated)}")
        print(f"   Processing time: {result.processing_time:.1f}s")

        if result.token_usage:
            print(f"   Tokens: {result.token_usage['input']} in, {result.token_usage['output']} out")

        if result.error_message:
            print(f"   Error: {result.error_message}")

        # Update package status
        try:
            sys.path.append('/home/johnny5/Johny5Alive/integrations')
            from sherlock_status_updater import update_package_status

            if result.success:
                update_package_status(package_id, 'completed', {
                    'claims_extracted': result.claims_extracted,
                    'entities_found': result.entities_found,
                    'outputs': result.outputs_generated
                })
            else:
                update_package_status(package_id, 'failed', {
                    'error': result.error_message
                })
        except Exception as e:
            print(f"   ⚠️  Status update failed: {e}")

        return {
            "status": "completed" if result.success else "failed",
            "claims_extracted": result.claims_extracted,
            "entities_found": result.entities_found,
            "outputs": result.outputs_generated,
            "processing_time": result.processing_time,
            "error": result.error_message
        }

    except Exception as e:
        print(f"   ❌ Research execution failed: {e}")

        # Update package status to failed
        try:
            sys.path.append('/home/johnny5/Johny5Alive/integrations')
            from sherlock_status_updater import update_package_status
            update_package_status(package_id, 'failed', {'error': str(e)})
        except:
            pass

        return {"status": "failed", "error": str(e)}

def main():
    task = json.loads(sys.stdin.read())
    task_type = task.get("task")
    task_id = task.get("id", "unknown")

    if task_type not in ALLOWED:
        print(f"❌ Blocked task: {task_type}", file=sys.stderr)
        print(f"   Allowed: {', '.join(sorted(ALLOWED))}", file=sys.stderr)
        sys.exit(1)

    print(f"🔄 Processing task: {task_id} ({task_type})")

    # Route to appropriate handler
    handlers = {
        "repo_sync": handle_repo_sync,
        "squirt_batch": handle_squirt_batch,
        "sherlock_export": handle_sherlock_export,
        "sherlock_content_collection": handle_sherlock_content_collection,
        "sherlock_research_execution": handle_sherlock_research_execution,
        "lint": handle_lint,
        "backup": handle_backup,
        "llm_job": handle_llm_job
    }

    try:
        result = handlers[task_type](task.get("args", {}))

        # Log result
        print(f"\n✅ Task {task_id} completed")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n❌ Task {task_id} failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
