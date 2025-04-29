from collections import deque
import wikipediaapi
import requests
import json
import random
import os

class WikipediaGraph:
    def __init__(self, cache_file="wikigraph_cache.json"):
        """
        Initializes the WikipediaGraph object with an empty adjacency list.
        """
        self.cache_file = cache_file
        self.adj_list = {}
        self.start_page = None
        self.end_page = None

        # Load the cache if it exists
        if not self.load_cache(self.cache_file):
            print("No cache found, starting with an empty graph.")
            return None

    def build_graph_from_file(self, filepath):
        """
        Reads a file and builds an adjacency list representing Wikipedia page connections.

        Parameters
        ----------
        filepath : str
            The path to the file containing Wikipedia page connections.

        Note
        ------
            The file should be in tab-separated format with the following header/columns:
            page_id_from, page_title_from, page_id_to, page_title_to
        """
        with open(filepath, 'r', encoding='utf-8') as file:
            next(file)  # Skip header line
            for line in file:
                parts = line.strip().split('\t')
                if len(parts) != 4:
                    continue

                from_title = parts[1]
                to_title = parts[3]

                # Initialize empty lists if nodes are new
                if from_title not in self.adj_list:
                    self.adj_list[from_title] = []
                if to_title not in self.adj_list:
                    self.adj_list[to_title] = []

                # Add a directed edge
                self.adj_list[from_title].append(to_title)

        self.cache_data(self.cache_file)

    def cache_data(self, file_name):
        """
        Saves the current adjacency list to a JSON file.
        
        Parameters
        ----------
        file_name : str
            The name of the file where the graph will be saved.
        """
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(self.adj_list, f, ensure_ascii=False, indent=4)
            print(f"Graph cached successfully to {file_name}.")

    def load_cache(self, file_name):
        """
        Loads the graph data from a cache file if it exists.
        
        Parameters
        ----------
        file_name : str
            The name of the file from which to load the graph data.
        
        Returns
        -------
        bool
            True if the data was successfully loaded, False otherwise.
        """
        loaded = False
        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8') as f:
                self.adj_list = json.load(f)
                print(f"Graph loaded from cache at {file_name}.")
                loaded = True
        return loaded

    def get_connections(self, page_title):
        """
        Returns a list of pages that the given page links to.

        Parameters
        ----------
        page_title : str
            The title of the Wikipedia page.

        Returns
        -------
        list
            A list of titles of pages that the given page links to.
        """
        return self.adj_list.get(page_title, [])

    def find_shortest_path(self, start_page, end_page):
        """
        Finds the shortest path between two pages using BFS.

        Parameters
        ----------
        start_page : str
            The title of the starting Wikipedia page.

        end_page : str
            The title of the ending Wikipedia page.

        Returns
        -------
        list or None
            A list of page titles representing the shortest path, or None if no path exists.
        """
        self.start_page = start_page
        self.end_page = end_page

        if start_page not in self.adj_list or end_page not in self.adj_list: # One or both pages not in graph
            return None

        if start_page == end_page: # Start and end pages are the same
            return [0, [start_page]]

        queue = deque()
        queue.append((start_page, [start_page]))
        visited = set()

        while queue:
            current_page, path = queue.popleft()
            if current_page == end_page:
                return path

            visited.add(current_page)

            for neighbor in self.get_connections(current_page):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor])) # Add neighbor to path
                    visited.add(neighbor)

        return None  # No path found

    def print_shortest_path(self, start_page, end_page):
        """
        Prints the shortest path, using arrows to indicate direction, between two pages.

        Parameters
        ----------
        start_page : str
            The title of the starting Wikipedia page.

        end_page : str
            The title of the ending Wikipedia page.
        """
        path = self.find_shortest_path(start_page, end_page)
        if path:
            print(f"\nShortest path ({len(path) - 1} steps):")
            print(" → ".join(path))
        else:
            print("No path found between the given pages.")

    def get_out_degree(self, page_title):
        """
        Returns the out-degree (number of links to other pages) of a given page.

        Parameters
        ----------
        page_title : str
            The title of the Wikipedia page.

        Returns
        -------
        int
            The out-degree of the page.
        """
        return len(self.get_connections(page_title))

    def get_in_degree(self, page_title):
        """
        Returns the in-degree (number of links from other pages) of a given page.

        Parameters
        ----------
        page_title : str
            The title of the Wikipedia page.

        Returns
        -------
        int
            The in-degree of the page.
        """
        in_degree = 0
        for page_node, neighbors in self.adj_list.items():
            if page_title in neighbors:
                in_degree += 1
        return in_degree

    def print_degrees(self, page_title):
        """
        Prints the out-degree and in-degree of a given page.

        Parameters
        ----------
        page_title : str
            The title of the Wikipedia page.
        """
        out_degree = self.get_out_degree(page_title)
        in_degree = self.get_in_degree(page_title)
        print(f"\nPage: {page_title}")
        print(f"Out-degree (number of links to other pages): {out_degree}")
        print(f"In-degree (number of links from other pages): {in_degree}")

    def get_page_categories(self, page_title):
        """
        Fetches the categories of a given Wikipedia page.

        Parameters
        ----------
        page_title : str
            The title of the Wikipedia page.

        Returns
        -------
        set
            A set of categories the page belongs to.

        Note
        ------
        This function uses the Wikipedia API to fetch categories.
        """
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "categories",
            "cllimit": "max",
        }

        response = requests.get(url, params=params)
        data = response.json()

        if "query" not in data or "pages" not in data["query"]:
            return []

        categories = set()
        pages = data["query"]["pages"]

        for page_id, page_info in pages.items():
            if "categories" in page_info:
                categories = set(cat["title"] for cat in page_info["categories"])
        return categories

    def find_common_categories(self, title1, title2):
        """
        Finds and prints common categories between two Wikipedia pages.

        Parameters
        ----------
        title1 : str
            The title of the first Wikipedia page.

        title2 : str
            The title of the second Wikipedia page.
        """
        categories1 = self.get_page_categories(title1)
        categories2 = self.get_page_categories(title2)

        common = categories1.intersection(categories2)
        if common:
            print(f"\nCommon categories ({len(common)}) between {title1} and {title2}:")
            for category in common:
                print(category)
        else:
            print(f"\nNo common categories found between {title1} and {title2}.")

    def recommend_articles(self, page_title, top_n=3):
        """
        Prints the top n recommended articles based on shared links to a given page.

        Parameters
        ----------
        page_title : str
            The title of the Wikipedia page to base recommendations on.

        Note
        ------
        The function returns the top_n most similar pages based on shared links.
        The higher the number of shared links, the more similar the pages are.
        """
        if page_title not in self.adj_list:
            print(f"Page '{page_title}' not found in the network.")
            return None

        # Get the set of page links from the given page
        page_links = set(self.adj_list[page_title])

        similarities = []

        for other_page, other_links in self.adj_list.items():
            if other_page == page_title:
                continue  # Skip comparing the page to itself

            other_links_set = set(other_links)

            # Find how many links they share
            shared_links = page_links.intersection(other_links_set)
            similarity_score = len(shared_links)

            if similarity_score > 0:
                similarities.append((other_page, similarity_score))

        # If no articles share links with the given page, return None and print a message
        if not similarities:
            print(f"\nNo articles share links with '{page_title}'. We couldn't find any recommendations.")
            return None
    
        # Sort by most similar first
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return the top_n recommendations
        recommendations = similarities[:top_n]
        print(f"\nTop {top_n} recommendations based on links for '{page_title}':")
        for rec_page in recommendations:
            print(f"Page: {rec_page[0]}, Number of Shared Links: {rec_page[1]}")

class Explorer:
    def __init__(self, graph):
        """
        Initializes the Explorer with a WikipediaGraph object.

        Parameters
        ----------
        graph : WikipediaGraph
            The Wikipedia graph instance to interact with.
        """
        self.graph = graph

    def run(self):
        """
        Starts the Explorer application by running the main menu loop.
        """
        print("Welcome to the Wikipedia Explorer!")
        while True:
            self.start_navigation()

    def start_navigation(self):
        """
        Asks the user for start and end pages or picks random pages from the dataset to find the shortest path.
        """
        print("\nMain Menu:")
        print("1. Enter Start and End Pages")
        print("2. Pick Random Start and End Pages")
        print("3. Exit")

        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            start_page = input("Enter the start page title: ").strip()
            end_page = input("Enter the end page title: ").strip()
        elif choice == "2":
        # Randomly select a start page that has at least one neighbor
            valid_start_pages = [page for page, neighbors in self.graph.adj_list.items() if neighbors]
            if not valid_start_pages:
                print("No valid pages with neighbors found in the graph.")
                return None
            start_page = random.choice(valid_start_pages)
            end_page = random.choice(self.graph.adj_list[start_page])
        elif choice == "3":
            print("\nYou have exited the explorer.\nThanks for exploring the world of Wikipedia pages!")
            exit()
        else:
            print("Invalid choice. Please try again.")
            return None

        # Update the graph with the selected start and end pages
        self.graph.start_page = start_page
        self.graph.end_page = end_page

        # Find and display the shortest path
        self.graph.print_shortest_path(start_page, end_page)

        # After finding the path, move to the explore menu
        self.explore_menu()

    def explore_menu(self):
        """
        Provides additional exploration options after finding a path.
        """
        while True:
            print("\nExplore Menu:")
            print("1. Find another path")
            print("2. Find common categories between two pages")
            print("3. Get article recommendations based on a page")
            print("4. Find in-degree and out-degree of a page")  # <-- new option
            print("5. Exit")

            choice = input("Choose an option (1-5): ").strip()

            if choice == "1":
                return  # Go back to start_navigation
            elif choice == "2":
                self.handle_common_categories()
            elif choice == "3":
                self.handle_recommendations()
            elif choice == "4":
                self.handle_degrees()
            elif choice == "5":
                print("\nYou have exited the explorer.\nThanks for exploring the world of Wikipedia pages!")
                exit()
            else:
                print("\nInvalid choice. Please try again.")

    def handle_common_categories(self):
        """
        Handles finding common categories between two user-provided pages.
        Gives the user the option to use the current Start and End pages or input new ones to explore.
        """
        print("\nFind Common Categories:")
        print("1. Use the current Start and End pages")
        print("2. Enter two new pages manually")
        
        choice = input("Choose an option (1-2): ").strip()
        
        if choice == "1":
            if not self.graph.start_page or not self.graph.end_page:
                print("\nNo start and end pages have been set yet.")
                return None
            title1 = self.graph.start_page
            title2 = self.graph.end_page
        elif choice == "2":
            title1 = input("\nEnter the first page title: ").strip()
            title2 = input("Enter the second page title: ").strip()
        else:
            print("\nInvalid choice. Returning to Explore Menu.")
            return None

        self.graph.find_common_categories(title1, title2)

    def handle_recommendations(self):
        """
        Handles recommending articles based on a user-provided page.
        Allows user to use Start Page, End Page, or enter a new page manually.
        """
        print("\nGet Article Recommendations:")
        print("1. Use the current Start Page")
        print("2. Use the current End Page")
        print("3. Enter a new page manually")

        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            if not self.graph.start_page:
                print("\nNo start page has been set yet.")
                return None
            page_title = self.graph.start_page
        elif choice == "2":
            if not self.graph.end_page:
                print("\nNo end page has been set yet.")
                return None
            page_title = self.graph.end_page
        elif choice == "3":
            page_title = input("\nEnter the page title to get recommendations for: ").strip()
        else:
            print("\nInvalid choice. Returning to Explore Menu.")
            return None

        try:
            top_n = int(input("\nHow many recommendations do you want to see? (default 3): ").strip())
        except ValueError:
            top_n = 5  # fallback if input fails

        self.graph.recommend_articles(page_title, top_n=top_n)

    def handle_degrees(self):
        """
        Handles displaying the in-degree and out-degree of a user-provided page.
        Allows user to use Start Page, End Page, or enter a new page manually.
        """
        print("\nFind In/Out Degree of a Page:")
        print("1. Use the current Start Page")
        print("2. Use the current End Page")
        print("3. Enter a new page manually")

        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            if not self.graph.start_page:
                print("\nNo start page has been set yet.")
                return None
            page_title = self.graph.start_page
        elif choice == "2":
            if not self.graph.end_page:
                print("\nNo end page has been set yet.")
                return None
            page_title = self.graph.end_page
        elif choice == "3":
            page_title = input("\nEnter the page title: ").strip()
        else:
            print("\nInvalid choice. Returning to Explore Menu.")
            return None

        self.graph.print_degrees(page_title)


def main():
    """
    Main function to run the Wikipedia Explorer application.
    """
    # Initialize the WikipediaGraph object and load the cache if available
    graph = WikipediaGraph(cache_file='wikigraph_cache.json')
    if not graph.adj_list:
        graph.build_graph_from_file('wikilink_graph.2012-03-01.csv')

    # Run the Explorer application
    explorer = Explorer(graph)
    explorer.run()

if __name__ == "__main__":
    main()