"""Extract CodeEntity objects and relationships from ASTNode trees."""

import hashlib
from typing import Any, Dict, List, Optional, Tuple

from src.models.code_entity import CodeEntity, EntityType
from src.models.source_location import SourceLocation
from src.parsing.ast_nodes import ASTNode, NodeType
from src.graph.relationship import RelationshipType
from src.graph.extraction_result import ExtractionResult


# NodeType -> EntityType mapping for extractable nodes
_NODE_TO_ENTITY: Dict[NodeType, EntityType] = {
    NodeType.MODULE: EntityType.MODULE,
    NodeType.CLASS: EntityType.CLASS,
    NodeType.FUNCTION: EntityType.FUNCTION,
    NodeType.METHOD: EntityType.METHOD,
    NodeType.CONSTRUCTOR: EntityType.CONSTRUCTOR,
    NodeType.FIELD: EntityType.FIELD,
    NodeType.PARAMETER: EntityType.PARAMETER,
    NodeType.IMPORT: EntityType.IMPORT,
}

# NodeTypes that represent control-flow containers (classes/functions)
_CONTAINER_TYPES = {
    NodeType.MODULE,
    NodeType.CLASS,
    NodeType.FUNCTION,
    NodeType.METHOD,
    NodeType.CONSTRUCTOR,
}


class EntityExtractor:
    """Extracts CodeEntity objects and relationships from an ASTNode tree.

    Walks the AST depth-first, creating entities for significant nodes
    and discovering relationships from the tree structure.
    """

    def extract(self, ast_root: ASTNode, file_path: str) -> ExtractionResult:
        """Extract entities and relationships from an AST root.

        Args:
            ast_root: Root ASTNode (typically a MODULE node).
            file_path: Path to the source file.

        Returns:
            ExtractionResult with entities and relationships.
        """
        self._entities: List[CodeEntity] = []
        self._relationships: List[Tuple[str, str, RelationshipType, Dict[str, Any]]] = []
        self._file_path = file_path
        self._language = ast_root.language or "unknown"

        self._walk(ast_root, parent_id=None)

        result = ExtractionResult(
            file_path=file_path,
            entities=list(self._entities),
            relationships=list(self._relationships),
        )
        # Clean up instance state
        self._entities = []
        self._relationships = []
        return result

    def _walk(self, node: ASTNode, parent_id: Optional[str]) -> Optional[str]:
        """Walk the AST, extracting entities and relationships.

        Args:
            node: Current ASTNode.
            parent_id: ID of the parent entity (if any).

        Returns:
            The entity ID if this node was extracted, else None.
        """
        entity_type = _NODE_TO_ENTITY.get(node.node_type)
        current_id = parent_id

        if entity_type is not None:
            entity = self._build_entity(node, entity_type, parent_id)
            self._entities.append(entity)
            current_id = entity.id

            # Add containment/structural relationships
            if parent_id is not None:
                rel_type = self._containment_rel_type(entity_type)
                self._relationships.append((parent_id, entity.id, rel_type, {}))

            # Extract inheritance from class nodes
            if entity_type in (EntityType.CLASS, EntityType.INTERFACE):
                self._extract_inheritance(node, entity.id)

            # Extract import relationships
            if entity_type == EntityType.IMPORT:
                self._extract_import_info(node, entity.id, parent_id)

        # Extract call relationships from CALL nodes
        if node.node_type == NodeType.CALL and parent_id is not None:
            self._extract_call(node, parent_id)

        # Recurse into children
        for child in node.children:
            self._walk(child, current_id)

        return current_id

    def _build_entity(
        self,
        node: ASTNode,
        entity_type: EntityType,
        parent_id: Optional[str],
    ) -> CodeEntity:
        """Build a CodeEntity from an ASTNode."""
        name = node.name or self._fallback_name(node, entity_type)
        entity_id = self._generate_id(entity_type, name, parent_id)

        location = SourceLocation(
            file_path=self._file_path,
            start_line=max(node.start_line, 1),
            end_line=max(node.end_line, node.start_line, 1),
            start_column=node.start_column,
            end_column=node.end_column,
            symbol_name=name,
        )

        loc = max(node.end_line - node.start_line + 1, 0)

        # Extract modifiers from attributes if present
        modifiers = self._extract_modifiers(node)
        signature = self._extract_signature(node, entity_type)
        docstring = self._extract_docstring(node)

        return CodeEntity(
            id=entity_id,
            name=name,
            entity_type=entity_type,
            location=location,
            language=self._language,
            parent_id=parent_id,
            modifiers=modifiers,
            signature=signature,
            docstring=docstring,
            lines_of_code=loc,
        )

    def _generate_id(
        self,
        entity_type: EntityType,
        name: str,
        parent_id: Optional[str],
    ) -> str:
        """Generate a deterministic entity ID."""
        key = f"{self._file_path}:{entity_type.value}:{name}"
        if parent_id:
            key += f":{parent_id}"
        digest = hashlib.sha256(key.encode()).hexdigest()[:12]
        return f"{entity_type.value}_{digest}"

    def _fallback_name(self, node: ASTNode, entity_type: EntityType) -> str:
        """Generate a fallback name when the node has no name."""
        if entity_type == EntityType.MODULE:
            return self._file_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if entity_type == EntityType.IMPORT:
            # Use the source text, truncated
            text = node.source_text.strip().replace("\n", " ")
            return text[:80] if text else "import"
        return f"anonymous_{node.start_line}"

    def _containment_rel_type(self, entity_type: EntityType) -> RelationshipType:
        """Determine the containment relationship type for an entity."""
        mapping = {
            EntityType.METHOD: RelationshipType.HAS_METHOD,
            EntityType.CONSTRUCTOR: RelationshipType.HAS_METHOD,
            EntityType.FIELD: RelationshipType.HAS_FIELD,
            EntityType.PARAMETER: RelationshipType.HAS_PARAMETER,
        }
        return mapping.get(entity_type, RelationshipType.CONTAINS)

    def _extract_call(self, node: ASTNode, caller_id: str) -> None:
        """Extract a call relationship from a CALL node."""
        callee_name = self._resolve_call_name(node)
        if callee_name:
            # Store as an unresolved reference using a placeholder target ID
            target_id = f"unresolved:{callee_name}"
            self._relationships.append(
                (
                    caller_id,
                    target_id,
                    RelationshipType.CALLS,
                    {"callee_name": callee_name},
                )
            )

    def _resolve_call_name(self, call_node: ASTNode) -> Optional[str]:
        """Extract the function/method name from a CALL node."""
        # Look for the first child that is an IDENTIFIER
        for child in call_node.children:
            if child.node_type == NodeType.IDENTIFIER and child.name:
                return child.name
            # For attribute access like obj.method(), look deeper
            if child.node_type == NodeType.UNKNOWN:
                # Check attributes for ts_type = 'attribute'
                ts_type = child.attributes.get("ts_type", "")
                if ts_type in ("attribute", "member_expression"):
                    return self._extract_attribute_name(child)
        return None

    def _extract_attribute_name(self, node: ASTNode) -> Optional[str]:
        """Extract the method name from an attribute access node."""
        # The last identifier child is typically the method name
        identifiers = [c for c in node.children if c.node_type == NodeType.IDENTIFIER and c.name]
        return identifiers[-1].name if identifiers else None

    def _extract_inheritance(self, class_node: ASTNode, class_id: str) -> None:
        """Extract inheritance relationships from a class node."""
        # Look for argument_list or superclass indicators in children
        for child in class_node.children:
            ts_type = child.attributes.get("ts_type", "")
            if ts_type in (
                "argument_list",
                "superclass",
                "class_heritage",
                "superclass_list",
                "super_interfaces",
                "extends_type",
            ):
                # Extract parent class names from identifiers
                for desc in child.get_descendants(NodeType.IDENTIFIER):
                    if desc.name:
                        target = f"unresolved:{desc.name}"
                        self._relationships.append(
                            (
                                class_id,
                                target,
                                RelationshipType.INHERITS,
                                {"parent_name": desc.name},
                            )
                        )

    def _extract_import_info(
        self,
        import_node: ASTNode,
        import_id: str,
        module_id: Optional[str],
    ) -> None:
        """Extract import relationship details."""
        if module_id is None:
            return
        # Link the module to the imported entity
        self._relationships.append(
            (
                module_id,
                import_id,
                RelationshipType.IMPORTS,
                {"source_text": import_node.source_text.strip()[:100]},
            )
        )

    def _extract_modifiers(self, node: ASTNode) -> List[str]:
        """Extract access modifiers from a node."""
        modifiers: List[str] = []
        for child in node.children:
            ts_type = child.attributes.get("ts_type", "")
            if ts_type == "modifiers" or ts_type == "modifier":
                modifiers.append(child.source_text.strip())
            elif ts_type in (
                "public",
                "private",
                "protected",
                "static",
                "final",
                "abstract",
            ):
                modifiers.append(ts_type)
        return modifiers

    def _extract_signature(self, node: ASTNode, entity_type: EntityType) -> Optional[str]:
        """Extract function/method signature."""
        if entity_type not in (
            EntityType.FUNCTION,
            EntityType.METHOD,
            EntityType.CONSTRUCTOR,
        ):
            return None
        # Use the first line of source text as signature
        first_line = node.source_text.split("\n")[0].strip()
        return first_line[:200] if first_line else None

    def _extract_docstring(self, node: ASTNode) -> Optional[str]:
        """Extract docstring from a function/class node."""
        # Look for the first string literal or comment child in a block
        for child in node.children:
            if child.node_type == NodeType.BLOCK:
                for block_child in child.children:
                    if block_child.node_type == NodeType.UNKNOWN:
                        ts_type = block_child.attributes.get("ts_type", "")
                        if ts_type == "expression_statement":
                            for expr_child in block_child.children:
                                if (
                                    expr_child.node_type == NodeType.LITERAL
                                    and expr_child.source_text.startswith(('"""', "'''", '"', "'"))
                                ):
                                    return expr_child.source_text.strip("\"' \n")
                    break  # Only check the first statement
        return None
