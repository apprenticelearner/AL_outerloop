from setuptools import setup, find_packages 
  
with open('requirements.txt') as f: 
    requirements = f.readlines() 
  
long_description = '...need to add description' 
  
setup( 
        name ='al_outerloop', 
        version ='0.0.1', 
        author ='Daniel Weitekamp', 
        author_email ='weitekamp@cmu.edu', 
        url ='https://github.com/apprenticelearner/AL_outerloop', 
        description ='Runs outerloop agents.', 
        long_description = long_description, 
        long_description_content_type ="text/markdown", 
        license ='MIT', 
        packages = find_packages(), 
        # scripts=['bin/altrain'],
        # entry_points ={ 
            
        # }, 
        # entry_points={
        #     "console_scripts": [
        #         "altrain = al_hostserver.altrain:pre_main"
        #     ]
        # },
        classifiers =( 
            "Programming Language :: Python :: 3", 
            "License :: OSI Approved :: MIT License", 
            "Operating System :: OS Independent", 
        ), 
        keywords ='apprentice learner outerloop', 
        install_requires = requirements, 
        zip_safe = False
) 