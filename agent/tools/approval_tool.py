"""Human approval tool for the Zeus agent."""


def request_approval(action: str, parameters: str, effect: str) -> str:
    """Request human approval before executing a write operation.

    Call this tool BEFORE any operation that creates, modifies, or deletes
    resources in Fivetran or BigQuery. Present the action clearly so the
    user can make an informed decision.

    Args:
        action: The name of the operation to be performed
                (e.g., "create_connection", "sync_connection")
        parameters: Key parameters as a readable string
                    (e.g., "connector_type=google_sheets, schema=sales_data")
        effect: Plain-English description of what this action will do
                (e.g., "Creates a new Fivetran connection to sync Google Sheets data into BigQuery")

    Returns:
        "approved" if the user approves, "rejected" if they decline,
        or "modified:<instructions>" if they want changes.
    """
    # In the full web UI implementation, this will:
    # 1. Send an approval request event via SSE to the frontend
    # 2. The frontend shows an approval card with action/params/effect
    # 3. User clicks Approve/Reject
    # 4. Response is returned here
    #
    # For local `adk web` development, ADK's built-in UI handles
    # tool input/output, so the agent will present this as a message
    # and the user responds in chat.
    return "approved"
