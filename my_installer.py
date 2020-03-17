import os

#pyinstaller -D -n "幸运飞艇-策略2" --clean strategy2_run.py

if __name__ == "__main__":
    from PyInstaller.__main__ import run

    images_dir = os.path.sep.join(['client','resource','images'])

    # add_files = [
    #     (images_dir + os.path.sep + '*.png',images_dir)
    # ]


    opts = [
        '-F',
        '-w',
        # '-D',
        '--add-data=%s;%s' % (os.path.join('client','resource', 'images', '*.png'),os.path.join('client','resource', 'images')),
        '--add-data=%s;%s' % (os.path.join('client', 'resource', 'sounds', '*.wav'), os.path.join('client', 'resource', 'sounds')),
        '--name=%s' % '幸运飞艇-策略2',
        '--icon=xyft.ico',
        '--clean',
        '-y',
        'strategy2_run.py'
    ]

    run(opts)