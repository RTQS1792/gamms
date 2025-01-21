import pygame


class GraphVisual:
    def __init__(self, graph, width=1980, height=1080):
        self.graph = graph
        self.width = width
        self.height = height
        self.screen = None
        self.screen = None
        self.zoom = 1
        # Find the min and max x, y coordinates for scaling
        self.x_min = min(node.x for node in self.graph.nodes.values())
        self.x_max = max(node.x for node in self.graph.nodes.values())
        self.y_min = min(node.y for node in self.graph.nodes.values())
        self.y_max = max(node.y for node in self.graph.nodes.values())
        self.offset = (0.0, 0.0)

    def GraphCenter(self):
        """Gets the center of a graph."""
        return (((self.x_max - self.x_min ) / 2) + self.x_min, ((self.y_max - self.y_min) / 2) + self.y_min)

    def setZoom(self, zoom: float):
        self.zoom = zoom
        return self.zoom
    
    def setGraph(self, graph):
        self.graph = graph
    
    def setCamera(self, camera):
        self.camera = camera

    def ScalePositionToScreen(self, position: tuple[float, float]) -> tuple[float, float]:
        """Scale a coordinate value to fit within the screen."""
        graph_center = self.GraphCenter()
        # Graph comes in the form of KM. Need to convert the KM to scale for M. One unit = 1m
        screen_scale = 111139 / 100

        map_position = (screen_scale * (position[0] - graph_center[0]),screen_scale * (position[1] - graph_center[1]))
        map_position = self.camera.world_to_screen(map_position[0] + self.camera.x, map_position[1] + self.camera.y)
        #map_position = (map_position[0] + self.offset[0], map_position[1] + self.offset[1])
        return map_position

    def draw_node(self, screen, node, color=(90, 90, 90), draw_id=False):
        # """Draw a node as a circle with a light greenish color."""
        position = (node.x, node.y)
        (x, y) = self.ScalePositionToScreen(position)
        pygame.draw.circle(screen, color, (int(x), int(y)), 4) 
        # Draw node ID
        if draw_id:
            font = pygame.font.Font(None, 15)
            text = font.render(str(node.id), True, (0, 0, 0))
            text_rect = text.get_rect(center=(int(x), int(y)+10))
            screen.blit(text, text_rect)

    def draw_edge(self, screen, edge):
        edge_color = (150, 150, 150)
        """Draw an edge as a curve or straight line based on the linestring."""
        source = self.graph.nodes[edge.source]
        target = self.graph.nodes[edge.target]
        # for x,y in edge.linestring.coords:
        #     print("Linestring: ",x,y)
        
        # If linestring is present, draw it as a curve
        if edge.linestring:
            #linestring[1:-1]
            linestring = [(source.x, source.y)] + [(x, y) for (x, y) in edge.linestring.coords] + [(target.x, target.y)]
            scaled_points = [
                (self.ScalePositionToScreen((x, y)))
                for x, y in linestring
            ]
            pygame.draw.aalines(screen, edge_color, False, scaled_points, 2)
        else:
            # Straight line
            source_position = (source.x, source.y)
            target_position = (target.x, target.y)
            (x1, y1) = self.ScalePositionToScreen(source_position)
            (x2, y2) = self.ScalePositionToScreen(target_position)
            pygame.draw.line(screen, edge_color, (int(x1), int(y1)), (int(x2), int(y2)), 2)

    def MoveGraphPosition(self, direction: tuple[float, float]):
        self.offset = (self.offset[0] + direction[0], self.offset[1] + direction[1])
        
    def draw_graph(self, screen, draw_id=False):
        """Draw the entire graph (edges and nodes)."""
        # Center of Graph:
        self.screen = screen
        for edge in self.graph.edges.values():
            self.draw_edge(screen, edge)
        for node in self.graph.nodes.values():
            self.draw_node(screen, node, draw_id=draw_id)
        


