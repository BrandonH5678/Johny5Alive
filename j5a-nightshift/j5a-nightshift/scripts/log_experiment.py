#!/usr/bin/env python3
    """
    Experiment Logging Script
    
    Logs experimental results for Strategic Principle 10 (AI Literacy).
    """
    
    import json
    from datetime import datetime
    from pathlib import Path
    
    
    def log_experiment(experiment_data: dict):
        """
        Log experiment to playbook
    
        Args:
            experiment_data: Experiment details and results
        """
        playbook_dir = Path("playbook/experiments")
        playbook_dir.mkdir(parents=True, exist_ok=True)
    
        # Generate filename
        date_str = datetime.now().strftime('%Y-%m-%d')
        exp_name = experiment_data.get('name', 'experiment').replace(' ', '_')
        filename = f"{date_str}_{exp_name}.md"
    
        # Generate markdown
        content = f"""# Experiment: {experiment_data.get('name')}
    
    **Date:** {date_str}
    **Status:** {experiment_data.get('status', 'completed')}
    
    ## Hypothesis
    {experiment_data.get('hypothesis', 'N/A')}
    
    ## Method
    {experiment_data.get('method', 'N/A')}
    
    ## Results
    {experiment_data.get('results', 'N/A')}
    
    ## Learnings
    {experiment_data.get('learnings', 'N/A')}
    
    ## Constitutional Alignment
    {experiment_data.get('constitutional_notes', 'N/A')}
    
    ---
    *Logged by log_experiment.py*
    """
    
        # Save file
        filepath = playbook_dir / filename
        with open(filepath, 'w') as f:
            f.write(content)
    
        print(f"✅ Experiment logged: {filepath}")
    
    
    def main():
        """Interactive experiment logging"""
        print("Experiment Logger")
        print("="*50)
    
        experiment = {
            'name': input("Experiment name: "),
            'hypothesis': input("Hypothesis: "),
            'method': input("Method: "),
            'results': input("Results: "),
            'learnings': input("Key learnings: "),
            'status': 'completed'
        }
    
        log_experiment(experiment)
    
    
    if __name__ == "__main__":
        main()
    