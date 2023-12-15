
from skimage import img_as_ubyte
from skimage.measure import label, regionprops
from skimage.color import label2rgb

def merge_small_labels(labelled_mask, min_size, verbose = True):
    """Merge labels less than threshold size
    Small labels are merged to their largest neighbor in order to
    discourage over-segmentation.
    Label sizes are dynamically monitored to prevent labels
    that become sufficiently large during merges from unnecessary
    merges

    Author: Ruihong Yuan
    """
    from skimage.measure import regionprops
    from skimage.segmentation import find_boundaries
    from skimage.morphology import dilation, square

    labels = labelled_mask.copy()

    label_areas = []
    small_labels = []
    for region in regionprops(labels, cache=False):
        area = region.area
        label_areas.append(area)
        if area < min_size:
            small_labels.append(region.label)

    merged_count = 0
    skipped_count = 0
    for label in small_labels:
        assert label_areas[label-1] != 0, "Label area is zero only when it has been merged"

        if label_areas[label-1] >= min_size:
            skipped_count += 1
            if verbose:
                print("Skipped", label, "because it has reached min_size after merging")
            continue

        # Find neighboring pixels (label boundary)
        label_boundaries = find_boundaries(labels == label)
        # Expand boundary for robustness
        expanded_boundaries = dilation(label_boundaries, square(3))

        # Collect label types of the boundary pixels
        neighbors = set(labels[expanded_boundaries].flat)
        # Remove background and this label
        neighbors.discard(0)
        neighbors.discard(label)

        if neighbors:
            # Find the largest neighbor label
            largest_neighbor = max(neighbors, key=lambda x: label_areas[x - 1])
            if verbose:
                print("Merged", label, "to", largest_neighbor)
            labels[labels == label] = largest_neighbor
            # Update label areas
            label_areas[largest_neighbor - 1] += label_areas[label - 1]
            label_areas[label - 1] = 0
            merged_count += 1

    if verbose:
        print("Total merged:", merged_count)
        print("Total skipped:", skipped_count)
    return labels

def label2rgb_bbox(labeled_image, image=None, **kwargs):
    """Create bounding boxes based on label2rgb"""
    colors = label2rgb(labeled_image, image=image, **kwargs)
    colors = img_as_ubyte(colors)

    im = colors.copy()
    RED = [255, 0, 0]
    for region in regionprops(labeled_image):
        min_y, min_x, max_y, max_x = region.bbox
        im[min_y:max_y, min_x, :] = RED
        im[min_y:max_y, max_x-1, :] = RED
        im[min_y, min_x:max_x, :] = RED
        im[max_y-1, min_x:max_x, :] = RED

    return im
