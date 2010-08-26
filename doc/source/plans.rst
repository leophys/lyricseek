Plans for the project
=====================

This is a sort of project of what the library should look like when finished.

* A decent name :)
* Low, if not none, dependencies
* There is a simple but powerful api

  * get_lyrics(artist='foo', album='asd', title='xyz', otherinfo='this', timeout=10)
    Just do it.
  * get_lyrics_fastest(... as above ...)
    The first site to give an 'OK' will return
  * get_lyrics_best(... as above ...)
    Try to catch as much information as possible
  * get_lyrics_all(... as above ...)
    Return all results (useful for user selection)

* It's not limited to lyrics, but supports artist info, cover, tabs, whatsoever
* Extensibility is provided through eggs

  * see http://base-art.net/Articles/64/ (only useful if you already know eggs)
  * plugin can be separate packages
  * any package can contain entrypoint for our library
  * each plugin is called a Retriever

* Retrievers run concurrently, results analysis is performed real*time

  * This way we can take "the fastest", or wait for the best
  * An asyncronous API should be provided
	* This way a software can see the lyrics coming in real*time when he is
	  calling get_lyrics_all, not having to wait for all the lyrics to be fetched
	  (it is especially useful because there will probably some plugin behaving
	  badly, and we don't want it to ruin our work). 
	  And, yeah, there is timeout, but it's not a complete solution

* A command*line utility provides the same functionalities 

  * Different outputs (human, colour, parseable)

* A C library that wraps the python one
