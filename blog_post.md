# Teaching Claude Code to See in Windows: Automating UI Development with Screenshots in WSL

Claude Code has revolutionized how developers interact with their codebases, offering intelligent assistance for everything from debugging to feature implementation. For those unfamiliar, Claude Code is Anthropic's official Command Line Interface (CLI) tool that brings Claude's capabilities directly to your development environment, allowing for seamless code analysis, generation, and iteration. While Claude Code excels at understanding and manipulating code, one challenge remains: how do you get it to evaluate visual interfaces when browser-based MCP servers aren't available?

If you're developing desktop applications on Windows (whether using PyQt, Tkinter, Electron, or any other framework) you've likely encountered this limitation. Currently, in order to use Claude Code on Windows, you must install WSL with a Linux distribution, such as Ubuntu, to be able to use Claude Code. Setting up this environment requires some initial configuration, but the comprehensive setup process is well documented in [this helpful video guide](https://www.youtube.com/watch?v=lQmsLSR13ac) and the [official Claude Code installation instructions](https://docs.anthropic.com/en/docs/claude-code/getting-started).

## The Desktop Development Challenge

Desktop application development presents a unique challenge for AI-assisted development. Unlike web applications where browser automation tools can capture and analyze interfaces, desktop applications require different approaches. When you're iterating on UI design (adjusting layouts, refining color schemes, or ensuring accessibility compliance) you need a way for Claude Code to actually see what you've built.

This is where a custom screenshot solution becomes invaluable. By implementing a screenshot capability that works within the WSL environment, you can create a feedback loop where Claude Code can:

- Launch your application
- Capture visual snapshots of the interface
- Analyze design elements for accessibility, visual hierarchy, and user experience principles
- Suggest improvements based on modern design practices
- Implement changes and repeat the process

The result is that after a single run, you get most of the way towards a beautiful, tailored interface. This approach transforms Claude Code from a code-only assistant into a comprehensive UI development partner.

## The Setup Requirements

To enable this workflow, you'll need two key components in your project:

1. **An updated `CLAUDE.md` file** that includes instructions for screenshot capture. The exact code section to include in your `CLAUDE.md` is provided at the end of this post.
2. **A `take_screenshot.py` script** that handles the technical details of capturing screenshots in the WSL environment, including proper DPI scaling support. This is also included at the end of the post.

These components work together to give Claude Code the context and tools it needs to understand your visual interface and provide meaningful feedback.

## Putting It All Together: A Complete UI Iteration Prompt

Once you have your screenshot infrastructure in place, you can use prompts like this to create a complete UI development feedback loop:

```
I need you to help me improve the user interface of my desktop application. Please follow these steps in order:

1. **Launch the application**: Start the interface by running the appropriate command for my project
2. **Capture the current state**: Take a screenshot of the application using the take_screenshot.py script
3. **Analyze the interface**: Find the UI for this application in the screenshot, then review the UI screenshot for:
   - Visual hierarchy and information architecture
   - Color contrast and accessibility compliance
   - Element spacing, alignment, and proportions
   - Typography choices and readability
   - User experience flow and intuitive navigation
   - Consistency with modern design principles
   - Responsive behavior (if applicable)
   - (Optional) make the UI consistent with the interface in `link_to_example.png`
4. **Develop improvement plan**: Create a prioritized list of specific UI improvements with rationale
5. **Validate the plan**: Review your suggestions against established design principles and ensure they're technically feasible with the current framework
6. **Close the application**: Properly shut down the interface
7. **Implement changes**: Make the necessary code modifications to address the identified improvements
8. **Iterate**: Repeat this entire process until the interface meets professional standards and follows best practices

For each iteration, please commit your changes with descriptive commit messages so we can track the evolution of the interface and easily revert if needed.
```

This structured approach ensures comprehensive evaluation while maintaining a clear development workflow.

## Best Practices and Safety Nets

The iterative nature of AI-assisted UI development means you'll be making frequent changes to your codebase. This makes version control absolutely critical. Always use Git and commit after each iteration—this allows you to review each change Claude Code makes and provides easy rollback points if any modifications don't meet your expectations or introduce unexpected regressions.

The combination of screenshot feedback and systematic iteration creates a powerful development workflow that can dramatically accelerate UI refinement while maintaining code quality and design standards.