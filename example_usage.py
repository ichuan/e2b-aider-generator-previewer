"""
Example usage script for E2B Aider Code Generator.
"""

from e2b_aider_generator import E2BAiderClient


def main():
    """Example usage of the E2B Aider Code Generator."""
    
    # Initialize client with custom settings
    print("🚀 Initializing E2B Aider client with custom settings...")
    client = E2BAiderClient(
        openai_model="gpt-3.5-turbo",  # Use a cheaper model for examples
        openai_api_base=None  # Use default OpenAI API
    )
    
    # Example 1: Simple hello world program
    print("\n📝 Example 1: Creating a simple hello world program")
    result1 = client.generate_code(
        prompt=(
            "Create a Python program that prints 'Hello, World!' and "
            "asks for the user's name"
        )
    )
    
    if result1.success:
        print("✅ Success! Generated files:")
        for filename, content in result1.generated_files.items():
            print(f"  📄 {filename}:")
            print(f"     {content[:100]}{'...' if len(content) > 100 else ''}")
    else:
        print(f"❌ Failed: {result1.error_message}")
    
    # Example 2: Flask web application
    print("\n🌐 Example 2: Creating a Flask web application")
    result2 = client.generate_code(
        prompt=(
            "Create a simple Flask web application with a homepage that shows "
            "'Welcome to Flask!' and an about page. Include requirements.txt."
        )
    )
    
    if result2.success:
        print("✅ Success! Generated files:")
        for filename, content in result2.generated_files.items():
            print(f"  📄 {filename}")
            if filename.endswith('.py'):
                print(f"     {content[:150]}{'...' if len(content) > 150 else ''}")
            elif filename.endswith('.html'):
                print(f"     {content[:100]}{'...' if len(content) > 100 else ''}")
            else:
                print(f"     {content}")
    else:
        print(f"❌ Failed: {result2.error_message}")
    
    # Example 3: Data analysis script
    print("\n📊 Example 3: Creating a data analysis script")
    result3 = client.generate_code(
        prompt=(
            "Create a Python script that generates sample data, performs basic "
            "statistical analysis, and creates a simple visualization using matplotlib"
        )
    )
    
    if result3.success:
        print("✅ Success! Generated files:")
        for filename, content in result3.generated_files.items():
            print(f"  📄 {filename}:")
            print(f"     {content[:150]}{'...' if len(content) > 150 else ''}")
    else:
        print(f"❌ Failed: {result3.error_message}")
    
    # Example 4: Custom API configuration
    print("\n⚙️  Example 4: Using custom API configuration")
    custom_client = E2BAiderClient(
        openai_model="gpt-4",
        openai_api_base="https://api.example.com/v1"  # Example custom API
    )
    
    result4 = custom_client.generate_code(
        prompt="Create a simple configuration file parser"
    )
    
    if result4.success:
        print("✅ Success! Generated files with custom API config:")
        for filename, content in result4.generated_files.items():
            print(f"  📄 {filename}")
    else:
        print(f"❌ Failed: {result4.error_message}")
    
    print("\n📊 Summary:")
    total_time = (
        result1.execution_time + result2.execution_time + 
        result3.execution_time + result4.execution_time
    )
    print(f"   Total execution time: {total_time:.2f} seconds")
    print(f"   Example 1: {'✅' if result1.success else '❌'}")
    print(f"   Example 2: {'✅' if result2.success else '❌'}")
    print(f"   Example 3: {'✅' if result3.success else '❌'}")
    print(f"   Example 4: {'✅' if result4.success else '❌'}")


if __name__ == "__main__":
    main()