-- Migration: Fix agent name case sensitivity in single agent constraint
-- Purpose: Make agent validation case-insensitive (Scar = scar = SCAR)
-- Bug: Currently "Scar" != "scar" causes "Only one agent allowed" error

-- Drop existing trigger
DROP TRIGGER IF EXISTS single_agent_constraint ON agents;

-- Recreate function with case-insensitive comparison
CREATE OR REPLACE FUNCTION enforce_single_agent()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    -- Only check on INSERT of NEW agent (not existing one)
    IF TG_OP = 'INSERT' THEN
        -- Check if this is a different agent than existing (case-insensitive)
        IF EXISTS (
            SELECT 1 FROM agents 
            WHERE LOWER(agent_name) != LOWER(NEW.agent_name)
        ) THEN
            RAISE EXCEPTION 'Only one agent allowed in SupaBrain. Current agent: %, attempted: % (Note: Agent names are case-insensitive)',
                (SELECT agent_name FROM agents LIMIT 1), NEW.agent_name;
        END IF;
    END IF;
    RETURN NEW;
END;
$function$;

-- Recreate trigger
CREATE TRIGGER single_agent_constraint
    BEFORE INSERT ON agents
    FOR EACH ROW
    EXECUTE FUNCTION enforce_single_agent();

COMMENT ON FUNCTION enforce_single_agent() IS 'Enforces single-agent constraint with case-insensitive comparison';
